from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from typing_extensions import assert_never

from usethis._console import box_print, info_print, tick_print
from usethis._integrations.backend.uv.used import is_uv_used
from usethis._integrations.ci.bitbucket.anchor import (
    ScriptItemAnchor as BitbucketScriptItemAnchor,
)
from usethis._integrations.ci.bitbucket.schema import Script as BitbucketScript
from usethis._integrations.ci.bitbucket.schema import Step as BitbucketStep
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.pre_commit.schema import HookDefinition, Language, LocalRepo
from usethis._integrations.project.layout import get_source_dir_str
from usethis._tool.base import Tool
from usethis._tool.config import (
    ConfigEntry,
    ConfigItem,
    ConfigSpec,
    ensure_file_manager_exists,
)
from usethis._tool.pre_commit import PreCommitConfig
from usethis._types.deps import Dependency

if TYPE_CHECKING:
    from usethis._io import KeyValueFileManager
    from usethis._tool.rule import Rule


class DeptryTool(Tool):
    # https://github.com/fpgmaas/deptry
    @property
    def name(self) -> str:
        return "deptry"

    def print_how_to_use(self) -> None:
        _dir = get_source_dir_str()
        install_method = self.get_install_method()
        if install_method == "pre-commit":
            if is_uv_used():
                box_print(
                    f"Run 'uv run pre-commit run deptry --all-files' to run {self.name}."
                )
            else:
                box_print(
                    f"Run 'pre-commit run deptry --all-files' to run {self.name}."
                )
        elif install_method == "devdep" or install_method is None:
            if is_uv_used():
                box_print(f"Run 'uv run deptry {_dir}' to run deptry.")
            else:
                box_print(f"Run 'deptry {_dir}' to run deptry.")
        else:
            assert_never(install_method)

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return [Dependency(name="deptry")]

    def get_config_spec(self) -> ConfigSpec:
        # https://deptry.com/usage/#configuration
        return ConfigSpec.from_flat(
            file_managers=[PyprojectTOMLManager()],
            resolution="first",
            config_items=[
                ConfigItem(
                    description="Overall config",
                    root={Path("pyproject.toml"): ConfigEntry(keys=["tool", "deptry"])},
                )
            ],
        )

    def get_pre_commit_config(self) -> PreCommitConfig:
        _dir = get_source_dir_str()
        return PreCommitConfig.from_single_repo(
            LocalRepo(
                repo="local",
                hooks=[
                    HookDefinition(
                        id="deptry",
                        name="deptry",
                        entry=f"uv run --frozen --offline deptry {_dir}",
                        language=Language("system"),
                        always_run=True,
                        pass_filenames=False,
                    )
                ],
            ),
            requires_venv=True,
            inform_how_to_use_on_migrate=False,
        )

    def get_bitbucket_steps(self) -> list[BitbucketStep]:
        _dir = get_source_dir_str()
        return [
            BitbucketStep(
                name=f"Run {self.name}",
                caches=["uv"],
                script=BitbucketScript(
                    [
                        BitbucketScriptItemAnchor(name="install-uv"),
                        f"uv run deptry {_dir}",
                    ]
                ),
            )
        ]

    def is_managed_rule(self, rule: Rule) -> bool:
        return rule.startswith("DEP") and rule[3:].isdigit()

    def select_rules(self, rules: list[Rule]) -> None:
        """Does nothing for deptry - all rules are automatically enabled by default."""
        if rules:
            info_print(f"All {self.name} rules are always implicitly selected.")

    def get_selected_rules(self) -> list[Rule]:
        """No notion of selection for deptry.

        This doesn't mean rules won't be enabled, it just means we don't keep track
        of selection for them.
        """
        return []

    def deselect_rules(self, rules: list[Rule]) -> None:
        """Does nothing for deptry - all rules are automatically enabled by default."""

    def ignore_rules(self, rules: list[Rule]) -> None:
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
        rules = sorted(set(rules) & set(self.get_ignored_rules()))

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

    def get_ignored_rules(self) -> list[Rule]:
        (file_manager,) = self.get_active_config_file_managers()
        keys = self._get_ignore_keys(file_manager)
        try:
            rules: list[Rule] = file_manager[keys]
        except (KeyError, FileNotFoundError):
            rules = []

        return rules

    def _get_ignore_keys(self, file_manager: KeyValueFileManager) -> list[str]:
        """Get the keys for the ignored rules in the given file manager."""
        if isinstance(file_manager, PyprojectTOMLManager):
            return ["tool", "deptry", "ignore"]
        else:
            msg = (
                f"Unknown location for ignored {self.name} rules for file manager "
                f"'{file_manager.name}' of type {file_manager.__class__.__name__}."
            )
            raise NotImplementedError(msg)
