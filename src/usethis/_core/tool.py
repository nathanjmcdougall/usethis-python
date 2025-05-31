"""Tool functions to add/remove tools to/from the project."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from usethis._config import usethis_config
from usethis._console import tick_print
from usethis._integrations.ci.bitbucket.used import is_bitbucket_used
from usethis._integrations.file.pyproject_toml.valid import ensure_pyproject_validity
from usethis._integrations.pre_commit.core import (
    install_pre_commit_hooks,
    remove_pre_commit_config,
    uninstall_pre_commit_hooks,
)
from usethis._integrations.pre_commit.hooks import (
    add_placeholder_hook,
    get_hook_ids,
)
from usethis._integrations.pytest.core import add_pytest_dir, remove_pytest_dir
from usethis._integrations.uv.call import call_uv_subprocess
from usethis._integrations.uv.init import ensure_pyproject_toml
from usethis._tool.all_ import ALL_TOOLS
from usethis._tool.impl.codespell import CodespellTool
from usethis._tool.impl.coverage_py import CoveragePyTool
from usethis._tool.impl.deptry import DeptryTool
from usethis._tool.impl.import_linter import ImportLinterTool
from usethis._tool.impl.pre_commit import PreCommitTool
from usethis._tool.impl.pyproject_fmt import PyprojectFmtTool
from usethis._tool.impl.pyproject_toml import PyprojectTOMLTool
from usethis._tool.impl.pytest import PytestTool
from usethis._tool.impl.requirements_txt import RequirementsTxtTool
from usethis._tool.impl.ruff import RuffTool
from usethis._tool.rule import RuleConfig

if TYPE_CHECKING:
    from usethis._tool.base import Tool

# Note - all these functions invoke ensure_pyproject_toml() at the start, since
# declaring dependencies in pyproject.toml requires that file to exist.


class UseToolFunc(Protocol):
    def __call__(self, *, remove: bool, how: bool) -> None:
        """A function that adds/removes a tool to/from the project.

        Args:
            remove: If True, remove the tool instead of adding it.
            how: If True, print how to use the tool instead of adding/removing it.
        """


def use_codespell(*, remove: bool = False, how: bool = False) -> None:
    tool = CodespellTool()

    if how:
        tool.print_how_to_use()
        return

    if not remove:
        ensure_pyproject_toml()

        if not PreCommitTool().is_used():
            tool.add_dev_deps()
            tool.update_bitbucket_steps()
        else:
            tool.add_pre_commit_repo_configs()

        tool.add_configs()
        tool.print_how_to_use()
    else:
        tool.remove_bitbucket_steps()
        tool.remove_configs()
        tool.remove_pre_commit_repo_configs()
        tool.remove_dev_deps()
        tool.remove_managed_files()


def use_coverage_py(*, remove: bool = False, how: bool = False) -> None:
    tool = CoveragePyTool()

    if how:
        tool.print_how_to_use()
        return

    if not remove:
        ensure_pyproject_toml()

        tool.add_test_deps()
        tool.add_configs()
        tool.print_how_to_use()
    else:
        tool.remove_configs()
        tool.remove_test_deps()
        tool.remove_managed_files()


def use_deptry(*, remove: bool = False, how: bool = False) -> None:
    tool = DeptryTool()

    if how:
        tool.print_how_to_use()
        return

    if not remove:
        ensure_pyproject_toml()

        tool.add_dev_deps()
        if PreCommitTool().is_used():
            tool.add_pre_commit_repo_configs()
        else:
            tool.update_bitbucket_steps()

        tool.print_how_to_use()
    else:
        tool.remove_pre_commit_repo_configs()
        tool.remove_configs()
        tool.remove_bitbucket_steps()
        tool.remove_dev_deps()
        tool.remove_managed_files()


def use_import_linter(*, remove: bool = False, how: bool = False) -> None:
    tool = ImportLinterTool()

    if how:
        tool.print_how_to_use()
        return

    if not remove:
        ensure_pyproject_toml()

        tool.add_dev_deps()
        tool.add_configs()
        if PreCommitTool().is_used():
            tool.add_pre_commit_repo_configs()
        else:
            tool.update_bitbucket_steps()

        tool.print_how_to_use()
    else:
        tool.remove_pre_commit_repo_configs()
        tool.remove_bitbucket_steps()
        tool.remove_configs()
        tool.remove_dev_deps()
        tool.remove_managed_files()


def use_pre_commit(*, remove: bool = False, how: bool = False) -> None:
    tool = PreCommitTool()

    if how:
        tool.print_how_to_use()
        return

    pyproject_fmt_tool = PyprojectFmtTool()
    codespell_tool = CodespellTool()
    requirements_txt_tool = RequirementsTxtTool()

    if not remove:
        ensure_pyproject_toml()

        tool.add_dev_deps()
        _add_all_tools_pre_commit_configs()

        # We will use pre-commit instead of project-installed dependencies:
        if pyproject_fmt_tool.is_used():
            pyproject_fmt_tool.remove_dev_deps()
            pyproject_fmt_tool.add_configs()
            pyproject_fmt_tool.print_how_to_use()
        if codespell_tool.is_used():
            codespell_tool.remove_dev_deps()
            codespell_tool.add_configs()
            codespell_tool.print_how_to_use()

        if requirements_txt_tool.is_used():
            requirements_txt_tool.print_how_to_use()

        if not get_hook_ids():
            add_placeholder_hook()

        install_pre_commit_hooks()

        tool.update_bitbucket_steps()
        if is_bitbucket_used():
            _remove_bitbucket_linter_steps_from_default()

        tool.print_how_to_use()
    else:
        tool.remove_bitbucket_steps()
        if is_bitbucket_used():
            _add_bitbucket_linter_steps_to_default()

        uninstall_pre_commit_hooks()

        remove_pre_commit_config()
        tool.remove_dev_deps()

        # Need to add a new way of running some hooks manually if they are not dev
        # dependencies yet - explain to the user.
        if pyproject_fmt_tool.is_used():
            pyproject_fmt_tool.add_dev_deps()
            pyproject_fmt_tool.print_how_to_use()
        if codespell_tool.is_used():
            codespell_tool.add_dev_deps()
            codespell_tool.print_how_to_use()

        # Likewise, explain how to manually generate the requirements.txt file, since
        # they're not going to do it via pre-commit anymore.
        if requirements_txt_tool.is_used():
            requirements_txt_tool.print_how_to_use()
        tool.remove_managed_files()


def _add_all_tools_pre_commit_configs():
    for _tool in ALL_TOOLS:
        if _tool.is_used():
            _tool.add_pre_commit_repo_configs()


def _add_bitbucket_linter_steps_to_default() -> None:
    # This order of adding tools should be synced with the order hard-coded
    # in the function which adds steps.
    if is_bitbucket_used():
        tools: list[Tool] = [PyprojectFmtTool(), DeptryTool(), RuffTool()]
        for tool in tools:
            if tool.is_used():
                tool.update_bitbucket_steps()


def _remove_bitbucket_linter_steps_from_default() -> None:
    # This order of removing tools should be synced with the order hard-coded
    # in the function which adds steps.
    PyprojectFmtTool().remove_bitbucket_steps()
    DeptryTool().remove_bitbucket_steps()
    RuffTool().remove_bitbucket_steps()


def use_pyproject_fmt(*, remove: bool = False, how: bool = False) -> None:
    tool = PyprojectFmtTool()

    if how:
        tool.print_how_to_use()
        return

    if not remove:
        ensure_pyproject_toml()

        if not PreCommitTool().is_used():
            tool.add_dev_deps()
            tool.update_bitbucket_steps()
        else:
            tool.add_pre_commit_repo_configs()

        tool.add_configs()
        tool.print_how_to_use()
    else:
        tool.remove_bitbucket_steps()
        tool.remove_configs()
        tool.remove_pre_commit_repo_configs()
        tool.remove_dev_deps()
        tool.remove_managed_files()


def use_pyproject_toml(*, remove: bool = False, how: bool = False) -> None:
    tool = PyprojectTOMLTool()

    if how:
        tool.print_how_to_use()
        return

    if not remove:
        ensure_pyproject_toml()

        ensure_pyproject_validity()
        tool.print_how_to_use()
    else:
        tool.remove_managed_files()


def use_pytest(*, remove: bool = False, how: bool = False) -> None:
    tool = PytestTool()

    if how:
        tool.print_how_to_use()
        return

    rule_config = tool.get_rule_config()

    if not remove:
        ensure_pyproject_toml()

        tool.add_test_deps()
        tool.add_configs()
        if RuffTool().is_used():
            RuffTool().select_rules(rule_config.get_all_selected())

        # deptry currently can't scan the tests folder for dev deps
        # https://github.com/fpgmaas/deptry/issues/302
        add_pytest_dir()

        PytestTool().update_bitbucket_steps()

        tool.print_how_to_use()

        if CoveragePyTool().is_used():
            CoveragePyTool().print_how_to_use()
    else:
        PytestTool().remove_bitbucket_steps()

        if RuffTool().is_used():
            RuffTool().deselect_rules(rule_config.selected)
        tool.remove_configs()
        tool.remove_test_deps()
        remove_pytest_dir()  # Last, since this is a manual step

        if CoveragePyTool().is_used():
            CoveragePyTool().print_how_to_use()
        tool.remove_managed_files()


def use_requirements_txt(*, remove: bool = False, how: bool = False) -> None:
    tool = RequirementsTxtTool()

    if how:
        tool.print_how_to_use()
        return

    path = Path.cwd() / "requirements.txt"

    if not remove:
        ensure_pyproject_toml()

        is_pre_commit = PreCommitTool().is_used()

        if is_pre_commit:
            tool.add_pre_commit_repo_configs()

        if not path.exists():
            # N.B. this is where a task runner would come in handy, to reduce duplication.
            if not (Path.cwd() / "uv.lock").exists() and not usethis_config.frozen:
                tick_print("Writing 'uv.lock'.")
                call_uv_subprocess(["lock"], change_toml=False)

            if not usethis_config.frozen:
                tick_print("Writing 'requirements.txt'.")
                call_uv_subprocess(
                    [
                        "export",
                        "--frozen",
                        "--no-dev",
                        "--output-file=requirements.txt",
                    ],
                    change_toml=False,
                )

        tool.print_how_to_use()

    else:
        tool.remove_pre_commit_repo_configs()
        tool.remove_managed_files()


def use_ruff(
    *,
    remove: bool = False,
    how: bool = False,
    minimal: bool = False,
    linter: bool = True,
    formatter: bool = True,
) -> None:
    """Add Ruff to the project.

    By default, sensible default rules are selected. The exceptions are when using the
    `minimal` option, or if rules are already selected, in which case they are left
    alone. However, if the existing rules are all pydocstyle rules (managed by the
    `usethis docstyle` interface, then the default rules will still be added).

    Args:
        remove: Remove Ruff configuration.
        how: Print how to use Ruff.
        minimal: Don't add any default rules.
        linter: Whether to add/remove the Ruff linter.
        formatter: Whether to add/remove the Ruff formatter.
    """
    tool = RuffTool()

    if how:
        tool.print_how_to_use()
        return

    # Only add ruff rules if the user doesn't already have a select/ignore list.
    # Otherwise, we should leave them alone. An exception is pydocstyle rules, since
    # these are the responsibility of the pydocstyle interface via `usethis docstyle`.
    if minimal:
        rule_config = RuleConfig()
    elif (
        # See docstring. Basically, `usethis docstyle` manages the pydocstyle rules,
        # so we want to allow the user to subsequently call `usethis tool ruff` and
        # still get non-minimal default rules.
        all(tool._is_pydocstyle_rule(rule) for rule in tool.get_selected_rules())
        # Another situation where we add default rules is when there are no rules
        # selected yet (and we haven't explicitly been requested to add minimal config).
        or not tool.get_selected_rules()
    ):
        rule_config = _get_basic_rule_config()
    else:
        rule_config = RuleConfig()

    if not remove:
        tool = RuffTool(
            linter_detection="always" if linter else "auto",
            formatter_detection="always" if formatter else "auto",
        )

        ensure_pyproject_toml()

        tool.add_dev_deps()
        tool.add_configs()

        if linter:
            tool.select_rules(rule_config.get_all_selected())
            tool.ignore_rules(rule_config.get_all_ignored())
        if PreCommitTool().is_used():
            tool.add_pre_commit_repo_configs()
        else:
            tool.update_bitbucket_steps()

        tool.print_how_to_use()
    else:
        tool = RuffTool(
            linter_detection="never" if not linter else "always",
            formatter_detection="never" if not formatter else "always",
        )

        tool.remove_pre_commit_repo_configs()
        tool.remove_bitbucket_steps()
        tool.remove_configs()
        tool.remove_dev_deps()
        tool.remove_managed_files()


def _get_basic_rule_config() -> RuleConfig:
    """Get the basic rule config for Ruff."""
    selected = [
        "A",
        "C4",
        "E4",
        "E7",
        "E9",
        "F",
        "FLY",
        "FURB",
        "I",
        "PLE",
        "PLR",
        "RUF",
        "SIM",
        "UP",
    ]
    for _tool in ALL_TOOLS:
        additional_selected = _tool.get_rule_config().get_all_selected()
        if additional_selected and _tool.is_used():
            selected += additional_selected
    ignored = [
        "PLR2004",  # https://github.com/nathanjmcdougall/usethis-python/issues/105
        "SIM108",  # https://github.com/nathanjmcdougall/usethis-python/issues/118
    ]
    return RuleConfig(selected=selected, ignored=ignored)
