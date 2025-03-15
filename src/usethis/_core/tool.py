from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from usethis._ci import (
    is_bitbucket_used,
    remove_bitbucket_pytest_steps,
    update_bitbucket_pytest_steps,
)
from usethis._config import usethis_config
from usethis._console import tick_print
from usethis._integrations.ci.bitbucket.steps import (
    add_bitbucket_steps_in_default,
    remove_bitbucket_steps_from_default,
)
from usethis._integrations.file.pyproject_toml.valid import ensure_pyproject_validity
from usethis._integrations.pre_commit.core import (
    install_pre_commit_hooks,
    remove_pre_commit_config,
    uninstall_pre_commit_hooks,
)
from usethis._integrations.pre_commit.hooks import (
    add_placeholder_hook,
    get_hook_names,
)
from usethis._integrations.pytest.core import add_pytest_dir, remove_pytest_dir
from usethis._integrations.ruff.rules import (
    deselect_ruff_rules,
    ignore_ruff_rules,
    select_ruff_rules,
)
from usethis._integrations.uv.call import call_uv_subprocess
from usethis._integrations.uv.init import ensure_pyproject_toml
from usethis._tool import (
    ALL_TOOLS,
    CodespellTool,
    CoverageTool,
    DeptryTool,
    PreCommitTool,
    PyprojectFmtTool,
    PyprojectTOMLTool,
    PytestTool,
    RequirementsTxtTool,
    RuffTool,
)

if TYPE_CHECKING:
    from usethis._tool import Tool


def use_codespell(*, remove: bool = False) -> None:
    tool = CodespellTool()

    ensure_pyproject_toml()

    if not remove:
        if not PreCommitTool().is_used():
            tool.add_dev_deps()
            if is_bitbucket_used():
                add_bitbucket_steps_in_default(tool.get_bitbucket_steps())
        else:
            tool.add_pre_commit_repo_configs()

        tool.add_configs()
        tool.print_how_to_use()
    else:
        remove_bitbucket_steps_from_default(tool.get_bitbucket_steps())
        tool.remove_configs()
        tool.remove_pre_commit_repo_configs()
        tool.remove_dev_deps()
        tool.remove_managed_files()


def use_coverage(*, remove: bool = False) -> None:
    tool = CoverageTool()

    ensure_pyproject_toml()

    if not remove:
        tool.add_test_deps()
        tool.add_configs()
        tool.print_how_to_use()
    else:
        tool.remove_configs()
        tool.remove_test_deps()
        tool.remove_managed_files()


def use_deptry(*, remove: bool = False) -> None:
    tool = DeptryTool()

    ensure_pyproject_toml()

    if not remove:
        tool.add_dev_deps()
        if PreCommitTool().is_used():
            tool.add_pre_commit_repo_configs()
        elif is_bitbucket_used():
            add_bitbucket_steps_in_default(tool.get_bitbucket_steps())

        tool.print_how_to_use()
    else:
        tool.remove_pre_commit_repo_configs()
        tool.remove_configs()
        remove_bitbucket_steps_from_default(tool.get_bitbucket_steps())
        tool.remove_dev_deps()
        tool.remove_managed_files()


def use_pre_commit(*, remove: bool = False) -> None:
    tool = PreCommitTool()
    pyproject_fmt_tool = PyprojectFmtTool()
    codespell_tool = CodespellTool()
    requirements_txt_tool = RequirementsTxtTool()

    ensure_pyproject_toml()

    if not remove:
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

        if not get_hook_names():
            add_placeholder_hook()

        install_pre_commit_hooks()

        if is_bitbucket_used():
            add_bitbucket_steps_in_default(tool.get_bitbucket_steps())
            _remove_bitbucket_linter_steps_from_default()

        tool.print_how_to_use()
    else:
        if is_bitbucket_used():
            remove_bitbucket_steps_from_default(tool.get_bitbucket_steps())
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
                add_bitbucket_steps_in_default(tool.get_bitbucket_steps())


def _remove_bitbucket_linter_steps_from_default() -> None:
    # This order of removing tools should be synced with the order hard-coded
    # in the function which adds steps.
    remove_bitbucket_steps_from_default(PyprojectFmtTool().get_bitbucket_steps())
    remove_bitbucket_steps_from_default(DeptryTool().get_bitbucket_steps())
    remove_bitbucket_steps_from_default(RuffTool().get_bitbucket_steps())


def use_pyproject_fmt(*, remove: bool = False) -> None:
    tool = PyprojectFmtTool()

    ensure_pyproject_toml()

    if not remove:
        if not PreCommitTool().is_used():
            tool.add_dev_deps()
            if is_bitbucket_used():
                add_bitbucket_steps_in_default(tool.get_bitbucket_steps())
        else:
            tool.add_pre_commit_repo_configs()

        tool.add_configs()
        tool.print_how_to_use()
    else:
        remove_bitbucket_steps_from_default(tool.get_bitbucket_steps())
        tool.remove_configs()
        tool.remove_pre_commit_repo_configs()
        tool.remove_dev_deps()
        tool.remove_managed_files()


def use_pyproject_toml(*, remove: bool = False) -> None:
    tool = PyprojectTOMLTool()

    ensure_pyproject_toml()

    if not remove:
        ensure_pyproject_toml()
        ensure_pyproject_validity()
        tool.print_how_to_use()
    else:
        tool.remove_managed_files()


def use_pytest(*, remove: bool = False) -> None:
    tool = PytestTool()

    ensure_pyproject_toml()

    if not remove:
        tool.add_test_deps()
        tool.add_configs()
        if RuffTool().is_used():
            select_ruff_rules(tool.get_associated_ruff_rules())

        # deptry currently can't scan the tests folder for dev deps
        # https://github.com/fpgmaas/deptry/issues/302
        add_pytest_dir()

        if is_bitbucket_used():
            update_bitbucket_pytest_steps()

        tool.print_how_to_use()

        if CoverageTool().is_used():
            CoverageTool().print_how_to_use()
    else:
        if is_bitbucket_used():
            remove_bitbucket_pytest_steps()

        if RuffTool().is_used():
            deselect_ruff_rules(tool.get_associated_ruff_rules())
        tool.remove_configs()
        tool.remove_test_deps()
        remove_pytest_dir()  # Last, since this is a manual step

        if CoverageTool().is_used():
            CoverageTool().print_how_to_use()
        tool.remove_managed_files()


def use_requirements_txt(*, remove: bool = False) -> None:
    tool = RequirementsTxtTool()

    ensure_pyproject_toml()

    path = Path.cwd() / "requirements.txt"

    if not remove:
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


def use_ruff(*, remove: bool = False) -> None:
    tool = RuffTool()

    ensure_pyproject_toml()

    rules = [
        "A",
        "C4",
        "E4",
        "E7",
        "E9",
        "EM",
        "F",
        "FURB",
        "I",
        "PLE",
        "PLR",
        "RUF",
        "SIM",
        "UP",
    ]
    for _tool in ALL_TOOLS:
        if _tool.is_used():
            rules += _tool.get_associated_ruff_rules()
    ignored_rules = [
        "PLR2004",  # https://github.com/nathanjmcdougall/usethis-python/issues/105
        "SIM108",  # https://github.com/nathanjmcdougall/usethis-python/issues/118
    ]

    if not remove:
        tool.add_dev_deps()
        tool.add_configs()
        select_ruff_rules(rules)
        ignore_ruff_rules(ignored_rules)
        if PreCommitTool().is_used():
            tool.add_pre_commit_repo_configs()
        elif is_bitbucket_used():
            add_bitbucket_steps_in_default(tool.get_bitbucket_steps())

        tool.print_how_to_use()
    else:
        tool.remove_pre_commit_repo_configs()
        remove_bitbucket_steps_from_default(tool.get_bitbucket_steps())
        tool.remove_configs()
        tool.remove_dev_deps()
        tool.remove_managed_files()
