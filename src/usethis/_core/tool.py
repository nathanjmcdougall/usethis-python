from pathlib import Path

from usethis._ci import (
    add_bitbucket_pre_commit_step,
    is_bitbucket_used,
    remove_bitbucket_pre_commit_step,
    remove_bitbucket_pytest_steps,
    update_bitbucket_pytest_steps,
)
from usethis._console import box_print, tick_print
from usethis._integrations.pre_commit.core import (
    install_pre_commit_hooks,
    remove_pre_commit_config,
    uninstall_pre_commit_hooks,
)
from usethis._integrations.pre_commit.hooks import add_placeholder_hook, get_hook_names
from usethis._integrations.pytest.core import add_pytest_dir, remove_pytest_dir
from usethis._integrations.ruff.rules import (
    deselect_ruff_rules,
    ignore_ruff_rules,
    select_ruff_rules,
)
from usethis._integrations.uv.call import call_uv_subprocess
from usethis._integrations.uv.deps import add_deps_to_group, remove_deps_from_group
from usethis._integrations.uv.init import ensure_pyproject_toml
from usethis._tool import (
    ALL_TOOLS,
    CoverageTool,
    DeptryTool,
    PreCommitTool,
    PyprojectFmtTool,
    PytestTool,
    RequirementsTxtTool,
    RuffTool,
)


def use_coverage(*, remove: bool = False) -> None:
    tool = CoverageTool()

    ensure_pyproject_toml()

    if not remove:
        add_deps_to_group(tool.dev_deps, "test")

        tool.add_pyproject_configs()

        if PytestTool().is_used():
            _coverage_instructions_pytest()
        else:
            _coverage_instructions_basic()
    else:
        tool.remove_pyproject_configs()
        remove_deps_from_group(tool.dev_deps, "test")


def _coverage_instructions_basic() -> None:
    box_print("Run 'coverage help' to see available coverage commands.")


def _coverage_instructions_pytest() -> None:
    box_print("Run 'pytest --cov' to run your tests with coverage.")


def use_deptry(*, remove: bool = False) -> None:
    tool = DeptryTool()

    ensure_pyproject_toml()

    if not remove:
        add_deps_to_group(tool.dev_deps, "dev")
        if PreCommitTool().is_used():
            tool.add_pre_commit_repo_configs()

        box_print("Run 'deptry src' to run deptry.")
    else:
        if PreCommitTool().is_used():
            tool.remove_pre_commit_repo_configs()
        remove_deps_from_group(tool.dev_deps, "dev")


def use_pre_commit(*, remove: bool = False) -> None:
    tool = PreCommitTool()

    ensure_pyproject_toml()

    if not remove:
        add_deps_to_group(tool.dev_deps, "dev")
        for _tool in ALL_TOOLS:
            if _tool.is_used():
                _tool.add_pre_commit_repo_configs()

        pyproject_fmt_tool = PyprojectFmtTool()
        if pyproject_fmt_tool.is_used():
            # We will use pre-commit instead of the dev-dep.
            remove_deps_from_group(pyproject_fmt_tool.get_unique_dev_deps(), "dev")
            pyproject_fmt_tool.add_pyproject_configs()
            _pyproject_fmt_instructions_pre_commit()

        if RequirementsTxtTool().is_used():
            _requirements_txt_instructions_pre_commit()

        if not get_hook_names():
            add_placeholder_hook()

        install_pre_commit_hooks()

        if is_bitbucket_used():
            add_bitbucket_pre_commit_step()

        box_print("Run 'pre-commit run --all-files' to run the hooks manually.")
    else:
        if is_bitbucket_used():
            remove_bitbucket_pre_commit_step()

        # Need pre-commit to be installed so we can uninstall hooks
        add_deps_to_group(tool.dev_deps, "dev")

        uninstall_pre_commit_hooks()
        remove_pre_commit_config()
        remove_deps_from_group(tool.dev_deps, "dev")

        # Need to add a new way of running some hooks manually if they are not dev
        # dependencies yet - explain to the user.
        if PyprojectFmtTool().is_used():
            _pyproject_fmt_instructions_basic()

        # Likewise, explain how to manually generate the requirements.txt file, since
        # they're not going to do it via pre-commit anymore.
        if RequirementsTxtTool().is_used():
            _requirements_txt_instructions_basic()


def use_pyproject_fmt(*, remove: bool = False) -> None:
    tool = PyprojectFmtTool()

    ensure_pyproject_toml()

    if not remove:
        is_pre_commit = PreCommitTool().is_used()

        if not is_pre_commit:
            add_deps_to_group(tool.dev_deps, "dev")
        else:
            tool.add_pre_commit_repo_configs()

        tool.add_pyproject_configs()

        if not is_pre_commit:
            _pyproject_fmt_instructions_basic()
        else:
            _pyproject_fmt_instructions_pre_commit()
    else:
        tool.remove_pyproject_configs()
        if PreCommitTool().is_used():
            tool.remove_pre_commit_repo_configs()
        remove_deps_from_group(tool.dev_deps, "dev")


def _pyproject_fmt_instructions_basic() -> None:
    box_print("Run 'pyproject-fmt pyproject.toml' to run pyproject-fmt.")


def _pyproject_fmt_instructions_pre_commit() -> None:
    box_print("Run 'pre-commit run pyproject-fmt --all-files' to run pyproject-fmt.")


def use_pytest(*, remove: bool = False) -> None:
    tool = PytestTool()

    ensure_pyproject_toml()

    if not remove:
        add_deps_to_group(tool.dev_deps, "test")
        tool.add_pyproject_configs()
        if RuffTool().is_used():
            select_ruff_rules(tool.get_associated_ruff_rules())

        # deptry currently can't scan the tests folder for dev deps
        # https://github.com/fpgmaas/deptry/issues/302
        add_pytest_dir()

        if is_bitbucket_used():
            update_bitbucket_pytest_steps()

        box_print(
            "Add test files to the '/tests' directory with the format 'test_*.py'."
        )
        box_print("Add test functions with the format 'test_*()'.")
        box_print("Run 'pytest' to run the tests.")

        if CoverageTool().is_used():
            _coverage_instructions_pytest()
    else:
        if is_bitbucket_used():
            remove_bitbucket_pytest_steps()

        if RuffTool().is_used():
            deselect_ruff_rules(tool.get_associated_ruff_rules())
        tool.remove_pyproject_configs()
        remove_deps_from_group(tool.dev_deps, "test")
        remove_pytest_dir()  # Last, since this is a manual step

        if CoverageTool().is_used():
            _coverage_instructions_basic()


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
            if not (Path.cwd() / "uv.lock").exists():
                tick_print("Writing 'uv.lock'.")
                call_uv_subprocess(["lock"])

            tick_print("Writing 'requirements.txt'.")
            call_uv_subprocess(
                [
                    "export",
                    "--frozen",
                    "--no-dev",
                    "--output-file=requirements.txt",
                ]
            )

        if not is_pre_commit:
            _requirements_txt_instructions_basic()
        else:
            _requirements_txt_instructions_pre_commit()
    else:
        if PreCommitTool().is_used():
            tool.remove_pre_commit_repo_configs()

        if path.exists() and path.is_file():
            tick_print("Removing 'requirements.txt'.")
            path.unlink()


def _requirements_txt_instructions_basic() -> None:
    box_print(
        "Run 'uv export --no-dev --output-file=requirements.txt' to write 'requirements.txt'."
    )


def _requirements_txt_instructions_pre_commit() -> None:
    box_print("Run the 'pre-commit run uv-export' to write 'requirements.txt'.")


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
        add_deps_to_group(tool.dev_deps, "dev")
        tool.add_pyproject_configs()
        select_ruff_rules(rules)
        ignore_ruff_rules(ignored_rules)
        if PreCommitTool().is_used():
            tool.add_pre_commit_repo_configs()

        box_print("Run 'ruff check --fix' to run the Ruff linter with autofixes.")
        box_print("Run 'ruff format' to run the Ruff formatter.")
    else:
        if PreCommitTool().is_used():
            tool.remove_pre_commit_repo_configs()
        tool.remove_pyproject_configs()  # N.B. this will remove the selected Ruff rules
        remove_deps_from_group(tool.dev_deps, "dev")
