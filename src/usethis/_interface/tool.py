from typing import Protocol

import typer

from usethis._config import offline_opt, quiet_opt, usethis_config
from usethis._config_file import files_manager
from usethis._console import err_print
from usethis._core.tool import (
    use_codespell,
    use_coverage,
    use_deptry,
    use_import_linter,
    use_pre_commit,
    use_pyproject_fmt,
    use_pyproject_toml,
    use_pytest,
    use_requirements_txt,
    use_ruff,
)
from usethis.errors import UsethisError

app = typer.Typer(help="Add and configure development tools, e.g. linters.")

remove_opt = typer.Option(
    False, "--remove", help="Remove the tool instead of adding it."
)

frozen_opt = typer.Option(False, "--frozen", help="Use the frozen dependencies.")


@app.command(
    name="codespell",
    help="Use the codespell spellchecker: detect common spelling mistakes.",
)
def codespell(
    remove: bool = remove_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
) -> None:
    with (
        usethis_config.set(offline=offline, quiet=quiet, frozen=frozen),
        files_manager(),
    ):
        _run_tool(use_codespell, remove=remove)


@app.command(name="coverage", help="Use coverage: a code coverage measurement tool.")
def coverage(
    remove: bool = remove_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
) -> None:
    with (
        usethis_config.set(offline=offline, quiet=quiet, frozen=frozen),
        files_manager(),
    ):
        _run_tool(use_coverage, remove=remove)


@app.command(
    name="deptry",
    help="Use the deptry linter: avoid missing or superfluous dependency declarations.",
)
def deptry(
    remove: bool = remove_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
) -> None:
    with (
        usethis_config.set(offline=offline, quiet=quiet, frozen=frozen),
        files_manager(),
    ):
        _run_tool(use_deptry, remove=remove)


@app.command(
    name="import-linter",
    help="Use Import Linter: enforce a self-imposed architecture on imports.",
)
def import_linter(
    remove: bool = remove_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
) -> None:
    with (
        usethis_config.set(offline=offline, quiet=quiet, frozen=frozen),
        files_manager(),
    ):
        _run_tool(use_import_linter, remove=remove)


@app.command(
    name="pre-commit",
    help="Use the pre-commit framework to manage and maintain pre-commit hooks.",
)
def pre_commit(
    remove: bool = remove_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
) -> None:
    with (
        usethis_config.set(offline=offline, quiet=quiet, frozen=frozen),
        files_manager(),
    ):
        _run_tool(use_pre_commit, remove=remove)


@app.command(
    name="pyproject-fmt",
    help="Use the pyproject-fmt linter: opinionated formatting of 'pyproject.toml' files.",
)
def pyproject_fmt(
    remove: bool = remove_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
) -> None:
    with (
        usethis_config.set(offline=offline, quiet=quiet, frozen=frozen),
        files_manager(),
    ):
        _run_tool(use_pyproject_fmt, remove=remove)


@app.command(
    name="pyproject.toml", help="Use a pyproject.toml file to configure the project."
)
def pyproject_toml(
    remove: bool = remove_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
) -> None:
    with (
        usethis_config.set(offline=offline, quiet=quiet, frozen=frozen),
        files_manager(),
    ):
        _run_tool(use_pyproject_toml, remove=remove)


@app.command(name="pytest", help="Use the pytest testing framework.")
def pytest(
    remove: bool = remove_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
) -> None:
    with (
        usethis_config.set(offline=offline, quiet=quiet, frozen=frozen),
        files_manager(),
    ):
        _run_tool(use_pytest, remove=remove)


@app.command(
    name="requirements.txt",
    help="Use a requirements.txt file exported from the uv lockfile.",
)
def requirements_txt(
    remove: bool = remove_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
) -> None:
    with (
        usethis_config.set(offline=offline, quiet=quiet, frozen=frozen),
        files_manager(),
    ):
        _run_tool(use_requirements_txt, remove=remove)


@app.command(
    name="ruff", help="Use Ruff: an extremely fast Python linter and code formatter."
)
def ruff(
    remove: bool = remove_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
) -> None:
    with (
        usethis_config.set(offline=offline, quiet=quiet, frozen=frozen),
        files_manager(),
    ):
        _run_tool(use_ruff, remove=remove)


class UseToolFunc(Protocol):
    def __call__(self, *, remove: bool) -> None: ...


def _run_tool(caller: UseToolFunc, *, remove: bool):
    try:
        caller(remove=remove)
    except UsethisError as err:
        err_print(err)
        raise typer.Exit(code=1) from None


ALL_TOOL_COMMANDS: list[str] = [
    "codespell",
    "coverage",
    "deptry",
    "import-linter",
    "pre-commit",
    "pyproject.toml",
    "pyproject-fmt",
    "pytest",
    "requirements.txt",
    "ruff",
]
