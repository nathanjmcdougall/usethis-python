from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

from usethis._config_file import (
    DotRuffTOMLManager,
    RuffTOMLManager,
)
from usethis._console import box_print, tick_print
from usethis._integrations.ci.bitbucket.anchor import (
    ScriptItemAnchor as BitbucketScriptItemAnchor,
)
from usethis._integrations.ci.bitbucket.schema import Pipe as BitbucketPipe
from usethis._integrations.ci.bitbucket.schema import Script as BitbucketScript
from usethis._integrations.ci.bitbucket.schema import Step as BitbucketStep
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.pre_commit.schema import (
    FileType,
    FileTypes,
    HookDefinition,
    Language,
    LocalRepo,
    UriRepo,
)
from usethis._integrations.uv.deps import (
    Dependency,
)
from usethis._integrations.uv.used import is_uv_used
from usethis._tool.base import Tool
from usethis._tool.config import (
    ConfigEntry,
    ConfigItem,
    ConfigSpec,
    ensure_file_manager_exists,
)

if TYPE_CHECKING:
    from usethis._io import KeyValueFileManager
    from usethis._tool.rule import Rule


class RuffTool(Tool):
    # https://github.com/astral-sh/ruff

    def __init__(self, linter: bool = True, formatter: bool = True):
        self.using_linter = linter
        self.using_formatter = formatter

        if not linter and not formatter:
            msg = f"{self.name} must be used as either a linter, a formatter, or both."
            raise NotImplementedError(msg)

    @property
    def name(self) -> str:
        return "Ruff"

    def print_how_to_use(self) -> None:
        if is_uv_used():
            if self.using_linter:
                box_print(
                    "Run 'uv run ruff check --fix' to run the Ruff linter with autofixes."
                )
            if self.using_formatter:
                box_print("Run 'uv run ruff format' to run the Ruff formatter.")
        else:
            if self.using_linter:
                box_print(
                    "Run 'ruff check --fix' to run the Ruff linter with autofixes."
                )
            if self.using_formatter:
                box_print("Run 'ruff format' to run the Ruff formatter.")

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return [Dependency(name="ruff")]

    def get_config_spec(self) -> ConfigSpec:
        # https://docs.astral.sh/ruff/configuration/#config-file-discovery

        line_length = 88

        return ConfigSpec.from_flat(
            file_managers=[
                DotRuffTOMLManager(),
                RuffTOMLManager(),
                PyprojectTOMLManager(),
            ],
            resolution="first",
            config_items=[
                ConfigItem(
                    description="Overall config",
                    root={
                        Path(".ruff.toml"): ConfigEntry(keys=[]),
                        Path("ruff.toml"): ConfigEntry(keys=[]),
                        Path("pyproject.toml"): ConfigEntry(keys=["tool", "ruff"]),
                    },
                ),
                ConfigItem(
                    description="Line length",
                    root={
                        Path(".ruff.toml"): ConfigEntry(
                            keys=["line-length"], get_value=lambda: line_length
                        ),
                        Path("ruff.toml"): ConfigEntry(
                            keys=["line-length"], get_value=lambda: line_length
                        ),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "ruff", "line-length"],
                            get_value=lambda: line_length,
                        ),
                    },
                ),
            ],
        )

    def get_managed_files(self) -> list[Path]:
        return [Path(".ruff.toml"), Path("ruff.toml")]

    def get_pre_commit_repos(self) -> list[LocalRepo | UriRepo]:
        repos = []
        if self.using_linter:
            repos.append(
                LocalRepo(
                    repo="local",
                    hooks=[
                        HookDefinition(
                            id="ruff",
                            name="ruff",
                            entry="uv run --frozen --offline ruff check --fix --force-exclude",
                            language=Language("system"),
                            types_or=FileTypes(
                                [
                                    FileType("python"),
                                    FileType("pyi"),
                                    FileType("jupyter"),
                                ]
                            ),
                            always_run=True,
                            require_serial=True,
                        ),
                    ],
                )
            )
        if self.using_formatter:
            repos.append(
                LocalRepo(
                    repo="local",
                    hooks=[
                        HookDefinition(
                            id="ruff-format",
                            name="ruff-format",
                            entry="uv run --frozen --offline ruff format --force-exclude",
                            language=Language("system"),
                            types_or=FileTypes(
                                [
                                    FileType("python"),
                                    FileType("pyi"),
                                    FileType("jupyter"),
                                ]
                            ),
                            always_run=True,
                            require_serial=True,
                        ),
                    ],
                )
            )
        return repos

    def get_bitbucket_steps(self) -> list[BitbucketStep]:
        lines: list[str | BitbucketPipe | BitbucketScriptItemAnchor] = [
            BitbucketScriptItemAnchor(name="install-uv")
        ]

        if self.using_linter:
            lines.append("uv run ruff check --fix")
        if self.using_formatter:
            lines.append("uv run ruff format")

        return [
            BitbucketStep(
                name=f"Run {self.name}",
                caches=["uv"],
                script=BitbucketScript(lines),
            )
        ]

    def select_rules(self, rules: list[Rule]) -> None:
        """Add Ruff rules to the project."""
        rules = sorted(set(rules) - set(self.get_selected_rules()))

        if not rules:
            return

        rules_str = ", ".join([f"'{rule}'" for rule in rules])
        s = "" if len(rules) == 1 else "s"

        (file_manager,) = self.get_active_config_file_managers()
        ensure_file_manager_exists(file_manager)
        tick_print(
            f"Selecting {self.name} rule{s} {rules_str} in '{file_manager.name}'."
        )
        keys = self._get_select_keys(file_manager)
        file_manager.extend_list(keys=keys, values=rules)

    def ignore_rules(self, rules: list[Rule]) -> None:
        """Ignore Ruff rules in the project."""
        rules = sorted(set(rules) - set(self.get_ignored_rules()))

        if not rules:
            return

        rules_str = ", ".join([f"'{rule}'" for rule in rules])
        s = "" if len(rules) == 1 else "s"

        (file_manager,) = self.get_active_config_file_managers()
        ensure_file_manager_exists(file_manager)
        tick_print(
            f"Ignoring {self.name} rule{s} {rules_str} in '{file_manager.name}'."
        )
        keys = self._get_ignore_keys(file_manager)
        file_manager.extend_list(keys=keys, values=rules)

    def unignore_rules(self, rules: list[str]) -> None:
        """Unignore Ruff rules in the project."""
        rules = list(set(rules) & set(self.get_ignored_rules()))

        if not rules:
            return

        rules_str = ", ".join([f"'{rule}'" for rule in rules])
        s = "" if len(rules) == 1 else "s"

        (file_manager,) = self.get_active_config_file_managers()
        ensure_file_manager_exists(file_manager)
        tick_print(
            f"No longer ignoring {self.name} rule{s} {rules_str} in '{file_manager.name}'."
        )
        keys = self._get_ignore_keys(file_manager)
        file_manager.remove_from_list(keys=keys, values=rules)

    def deselect_rules(self, rules: list[Rule]) -> None:
        """Ensure Ruff rules are not selected in the project."""
        rules = list(set(rules) & set(self.get_selected_rules()))

        if not rules:
            return

        rules_str = ", ".join([f"'{rule}'" for rule in rules])
        s = "" if len(rules) == 1 else "s"

        (file_manager,) = self.get_active_config_file_managers()
        ensure_file_manager_exists(file_manager)
        tick_print(
            f"Deselecting {self.name} rule{s} {rules_str} in '{file_manager.name}'."
        )
        keys = self._get_select_keys(file_manager)
        file_manager.remove_from_list(keys=keys, values=rules)

    def get_selected_rules(self) -> list[Rule]:
        """Get the Ruff rules selected in the project."""
        (file_manager,) = self.get_active_config_file_managers()

        keys = self._get_select_keys(file_manager)
        try:
            rules: list[Rule] = file_manager[keys]
        except (KeyError, FileNotFoundError):
            rules = []

        return rules

    def get_ignored_rules(self) -> list[Rule]:
        """Get the Ruff rules ignored in the project."""
        (file_manager,) = self.get_active_config_file_managers()
        keys = self._get_ignore_keys(file_manager)
        try:
            rules: list[Rule] = file_manager[keys]
        except (KeyError, FileNotFoundError):
            rules = []

        return rules

    def set_docstyle(self, style: Literal["numpy", "google", "pep257"]) -> None:
        (file_manager,) = self.get_active_config_file_managers()

        keys = self._get_docstyle_keys(file_manager)
        if keys in file_manager and file_manager[keys] == style:
            # Already set properly
            return

        msg = f"Setting docstring style to '{style}' in '{file_manager.name}'."
        tick_print(msg)
        file_manager[self._get_docstyle_keys(file_manager)] = style

    def get_docstyle(self) -> Literal["numpy", "google", "pep257"] | None:
        """Get the docstring style set in the project."""
        (file_manager,) = self.get_active_config_file_managers()
        keys = self._get_docstyle_keys(file_manager)
        try:
            docstyle = file_manager[keys]
        except (KeyError, FileNotFoundError):
            docstyle = None

        if docstyle not in ("numpy", "google", "pep257"):
            # Docstyle is not set or is invalid
            return None

        return docstyle

    def _are_pydocstyle_rules_selected(self) -> bool:
        """Check if pydocstyle rules are selected in the configuration."""
        # If "ALL" is selected, or any rule whose alphabetical part is "D".
        rules = self.get_selected_rules()
        for rule in rules:
            if rule == "ALL":
                return True
            if self._is_pydocstyle_rule(rule):
                return True
        return False

    @staticmethod
    def _is_pydocstyle_rule(rule: Rule) -> bool:
        return [d for d in rule if d.isalpha()] == ["D"]

    def _get_select_keys(self, file_manager: KeyValueFileManager) -> list[str]:
        """Get the keys for the selected rules in the given file manager."""
        if isinstance(file_manager, PyprojectTOMLManager):
            return ["tool", "ruff", "lint", "select"]
        elif isinstance(file_manager, RuffTOMLManager | DotRuffTOMLManager):
            return ["lint", "select"]
        else:
            msg = (
                f"Unknown location for selected {self.name} rules for file manager "
                f"'{file_manager.name}' of type {file_manager.__class__.__name__}."
            )
            raise NotImplementedError(msg)

    def _get_ignore_keys(self, file_manager: KeyValueFileManager) -> list[str]:
        """Get the keys for the ignored rules in the given file manager."""
        if isinstance(file_manager, PyprojectTOMLManager):
            return ["tool", "ruff", "lint", "ignore"]
        elif isinstance(file_manager, RuffTOMLManager | DotRuffTOMLManager):
            return ["lint", "ignore"]
        else:
            msg = (
                f"Unknown location for ignored {self.name} rules for file manager "
                f"'{file_manager.name}' of type {file_manager.__class__.__name__}."
            )
            raise NotImplementedError(msg)

    def _get_docstyle_keys(self, file_manager: KeyValueFileManager) -> list[str]:
        """Get the keys for the docstyle rules in the given file manager."""
        if isinstance(file_manager, PyprojectTOMLManager):
            return ["tool", "ruff", "lint", "pydocstyle", "convention"]
        elif isinstance(file_manager, RuffTOMLManager | DotRuffTOMLManager):
            return ["lint", "pydocstyle", "convention"]
        else:
            msg = (
                f"Unknown location for {self.name} docstring style for file manager "
                f"'{file_manager.name}' of type {file_manager.__class__.__name__}."
            )
            raise NotImplementedError(msg)
