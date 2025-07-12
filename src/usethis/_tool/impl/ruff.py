from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

from typing_extensions import assert_never

from usethis._config_file import DotRuffTOMLManager, RuffTOMLManager
from usethis._console import box_print, tick_print
from usethis._integrations.backend.uv.used import is_uv_used
from usethis._integrations.ci.bitbucket.anchor import (
    ScriptItemAnchor as BitbucketScriptItemAnchor,
)
from usethis._integrations.ci.bitbucket.schema import Script as BitbucketScript
from usethis._integrations.ci.bitbucket.schema import Step as BitbucketStep
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.pre_commit.schema import (
    FileType,
    FileTypes,
    HookDefinition,
    Language,
    LocalRepo,
)
from usethis._tool.base import Tool
from usethis._tool.config import (
    ConfigEntry,
    ConfigItem,
    ConfigSpec,
    ensure_file_manager_exists,
)
from usethis._tool.pre_commit import PreCommitConfig, PreCommitRepoConfig
from usethis._types.deps import Dependency

if TYPE_CHECKING:
    from usethis._integrations.ci.bitbucket.schema import Pipe as BitbucketPipe
    from usethis._io import KeyValueFileManager
    from usethis._tool.rule import Rule, RuleConfig


class RuffTool(Tool):
    # https://github.com/astral-sh/ruff

    def __init__(
        self,
        linter_detection: Literal["auto", "always", "never"] = "auto",
        formatter_detection: Literal["auto", "always", "never"] = "auto",
    ):
        """Initialize the Ruff management class.

        Args:
            linter_detection: A method to determine whether the linter is being used. By
                              default, it will be determined using heuristics
                              automatically, but this can be over-ridden.
            formatter_detection: A method to determine whether the formatter is used. By
                                 default, it will be determined using heuristics
                                 automatically, but this can be over-ridden.
        """
        self.linter_detection: Literal["auto", "always", "never"] = linter_detection
        self.formatter_detection: Literal["auto", "always", "never"] = (
            formatter_detection
        )
        self.is_auto_detection = (linter_detection == "auto") and (
            formatter_detection == "auto"
        )

    @property
    def name(self) -> str:
        return "Ruff"

    def print_how_to_use(self) -> None:  # noqa: PLR0912
        install_method = self.get_install_method()
        if install_method == "pre-commit":
            if is_uv_used():
                if self.is_linter_used():
                    box_print(
                        "Run 'uv run pre-commit run ruff --all-files' to run the Ruff linter."
                    )
                if self.is_formatter_used():
                    box_print(
                        "Run 'uv run pre-commit run ruff-format' to run the Ruff formatter."
                    )
            else:
                if self.is_linter_used():
                    box_print(
                        "Run 'pre-commit run ruff --all-files' to run the Ruff linter."
                    )
                if self.is_formatter_used():
                    box_print(
                        "Run 'pre-commit run ruff-format' to run the Ruff formatter."
                    )
        elif install_method == "devdep" or install_method is None:
            if is_uv_used():
                if self.is_linter_used():
                    box_print(
                        "Run 'uv run ruff check --fix' to run the Ruff linter with autofixes."
                    )
                if self.is_formatter_used():
                    box_print("Run 'uv run ruff format' to run the Ruff formatter.")
            else:
                if self.is_linter_used():
                    box_print(
                        "Run 'ruff check --fix' to run the Ruff linter with autofixes."
                    )
                if self.is_formatter_used():
                    box_print("Run 'ruff format' to run the Ruff formatter.")
        else:
            assert_never(install_method)

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return [Dependency(name="ruff")]

    def get_config_spec(self) -> ConfigSpec:
        # https://docs.astral.sh/ruff/configuration/#config-file-discovery

        line_length = 88

        config_items = [
            ConfigItem(
                description="Overall config",
                root={
                    Path(".ruff.toml"): ConfigEntry(keys=[]),
                    Path("ruff.toml"): ConfigEntry(keys=[]),
                    Path("pyproject.toml"): ConfigEntry(keys=["tool", "ruff"]),
                },
                # If the detection method is "never" for either the linter or formatter,
                # then we shouldn't remove the overall config section. And when it comes
                # to adding, it will be added regardless since there are other config
                # subsections below.
                managed=not (
                    (self.linter_detection == "never")
                    or (self.formatter_detection == "never")
                ),
            ),
        ]
        if self.linter_detection == "always":
            config_items.extend(
                [
                    ConfigItem(
                        description="Linter config",
                        root={
                            Path(".ruff.toml"): ConfigEntry(keys=["lint"]),
                            Path("ruff.toml"): ConfigEntry(keys=["lint"]),
                            Path("pyproject.toml"): ConfigEntry(
                                keys=["tool", "ruff", "lint"]
                            ),
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
                ]
            )
        if self.formatter_detection == "always":
            config_items.extend(
                [
                    ConfigItem(
                        description="Formatter config",
                        root={
                            Path(".ruff.toml"): ConfigEntry(keys=["format"]),
                            Path("ruff.toml"): ConfigEntry(keys=["format"]),
                            Path("pyproject.toml"): ConfigEntry(
                                keys=["tool", "ruff", "format"]
                            ),
                        },
                    ),
                    ConfigItem(
                        description="Docstring Code Format",
                        root={
                            Path(".ruff.toml"): ConfigEntry(
                                keys=["format", "docstring-code-format"],
                                get_value=lambda: True,
                            ),
                            Path("ruff.toml"): ConfigEntry(
                                keys=["format", "docstring-code-format"],
                                get_value=lambda: True,
                            ),
                            Path("pyproject.toml"): ConfigEntry(
                                keys=[
                                    "tool",
                                    "ruff",
                                    "format",
                                    "docstring-code-format",
                                ],
                                get_value=lambda: True,
                            ),
                        },
                    ),
                ]
            )

        return ConfigSpec.from_flat(
            file_managers=[
                DotRuffTOMLManager(),
                RuffTOMLManager(),
                PyprojectTOMLManager(),
            ],
            resolution="first",
            config_items=config_items,
        )

    def get_managed_files(self) -> list[Path]:
        return [Path(".ruff.toml"), Path("ruff.toml")]

    def get_pre_commit_config(self) -> PreCommitConfig:
        repo_configs = []
        if self.is_linter_used():
            repo_configs.append(
                PreCommitRepoConfig(
                    repo=LocalRepo(
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
                    ),
                    requires_venv=True,
                )
            )
        if self.is_formatter_used():
            repo_configs.append(
                PreCommitRepoConfig(
                    repo=LocalRepo(
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
                    ),
                    requires_venv=True,
                )
            )
        return PreCommitConfig(
            repo_configs=repo_configs,
            inform_how_to_use_on_migrate=True,  # The pre-commit commands are not simpler than the venv-based commands
        )

    def get_bitbucket_steps(self) -> list[BitbucketStep]:
        shared_lines: list[str | BitbucketPipe | BitbucketScriptItemAnchor] = [
            BitbucketScriptItemAnchor(name="install-uv")
        ]

        steps = []
        if self.is_linter_used():
            lines = [*shared_lines, "uv run ruff check --fix"]
            step = BitbucketStep(
                name=f"Run {self.name}",
                caches=["uv"],
                script=BitbucketScript(lines),
            )
            steps.append(step)
        if self.is_formatter_used():
            lines = [*shared_lines, "uv run ruff format"]
            step = BitbucketStep(
                name=f"Run {self.name} Formatter",
                caches=["uv"],
                script=BitbucketScript(lines),
            )
            steps.append(step)

        return steps

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

    def ignore_rules_in_glob(self, rules: list[Rule], *, glob: str) -> None:
        """Ignore Ruff rules in the project for a specific glob pattern."""
        if not rules:
            return

        (file_manager,) = self.get_active_config_file_managers()
        ensure_file_manager_exists(file_manager)
        keys = self._get_per_file_ignore_keys(file_manager, glob=glob)
        file_manager.extend_list(keys=keys, values=rules)

    def apply_rule_config(self, rule_config: RuleConfig) -> None:
        """Apply the Ruff rules associated with a rule config to the project.

        Note, this will add both managed and unmanaged config.
        """
        self.select_rules(rule_config.get_all_selected())
        self.ignore_rules(rule_config.get_all_ignored())
        self.ignore_rules_in_glob(
            rule_config.tests_unmanaged_ignored, glob="*/tests/**"
        )

    def remove_rule_config(self, rule_config: RuleConfig) -> None:
        """Remove the Ruff rules associated with a rule config from the project.

        Note, this will not modify unmanaged config.
        """
        self.deselect_rules(rule_config.selected)
        self.unignore_rules(rule_config.ignored)

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
                f"'{file_manager.name}' of type '{file_manager.__class__.__name__}'."
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
                f"'{file_manager.name}' of type '{file_manager.__class__.__name__}'."
            )
            raise NotImplementedError(msg)

    def _get_per_file_ignore_keys(
        self, file_manager: KeyValueFileManager, *, glob: str
    ) -> list[str]:
        """Get the keys for the per-file ignored rules in the given file manager."""
        if isinstance(file_manager, PyprojectTOMLManager):
            return ["tool", "ruff", "lint", "per-file-ignores", glob]
        elif isinstance(file_manager, RuffTOMLManager | DotRuffTOMLManager):
            return ["lint", "per-file-ignores", glob]
        else:
            msg = (
                f"Unknown location for per-file ignored {self.name} rules for file manager "
                f"'{file_manager.name}' of type '{file_manager.__class__.__name__}'."
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
                f"'{file_manager.name}' of type '{file_manager.__class__.__name__}'."
            )
            raise NotImplementedError(msg)

    def is_linter_used(self) -> bool:
        """Check if the linter is used in the project.

        This assumes we already know that Ruff is used.
        """
        if self.linter_detection == "always":
            return True
        elif self.linter_detection == "never":
            return False
        elif self.linter_detection == "auto":
            pass
        else:
            assert_never(self.linter_detection)

        return self.is_linter_config_present() or (
            self.is_auto_detection and self.is_no_subtool_config_present()
        )

    def is_linter_config_present(self) -> bool:
        return self._is_config_spec_present(
            ConfigSpec.from_flat(
                file_managers=[
                    DotRuffTOMLManager(),
                    RuffTOMLManager(),
                    PyprojectTOMLManager(),
                ],
                resolution="first",
                config_items=[
                    ConfigItem(
                        description="Linter Config",
                        root={
                            Path(".ruff.toml"): ConfigEntry(keys=["lint"]),
                            Path("ruff.toml"): ConfigEntry(keys=["lint"]),
                            Path("pyproject.toml"): ConfigEntry(
                                keys=["tool", "ruff", "lint"]
                            ),
                        },
                    ),
                ],
            )
        )

    def is_formatter_used(self) -> bool:
        """Check if the formatter is used in the project.

        This assumes we already know that Ruff is used.
        """
        if self.formatter_detection == "always":
            return True
        elif self.formatter_detection == "never":
            return False
        elif self.formatter_detection == "auto":
            pass
        else:
            assert_never(self.formatter_detection)

        return self.is_formatter_config_present() or (
            self.is_auto_detection and self.is_no_subtool_config_present()
        )

    def is_formatter_config_present(self) -> bool:
        return self._is_config_spec_present(
            ConfigSpec.from_flat(
                file_managers=[
                    DotRuffTOMLManager(),
                    RuffTOMLManager(),
                    PyprojectTOMLManager(),
                ],
                resolution="first",
                config_items=[
                    ConfigItem(
                        description="Formatter Config",
                        root={
                            Path(".ruff.toml"): ConfigEntry(keys=["format"]),
                            Path("ruff.toml"): ConfigEntry(keys=["format"]),
                            Path("pyproject.toml"): ConfigEntry(
                                keys=["tool", "ruff", "format"]
                            ),
                        },
                    ),
                ],
            )
        )

    def is_no_subtool_config_present(self) -> bool:
        """Check if no subtool config is present."""
        return (
            not self.is_linter_config_present()
            and not self.is_formatter_config_present()
        )
