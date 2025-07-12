from __future__ import annotations

from typing import TYPE_CHECKING, Any

import typer

from usethis._options import (
    backend_opt,
    frozen_opt,
    how_opt,
    offline_opt,
    quiet_opt,
    remove_opt,
)
from usethis._types.backend import BackendEnum

if TYPE_CHECKING:
    from usethis._core.tool import UseToolFunc

app = typer.Typer(help="Add and configure individual tools.", add_completion=False)

# ruff: noqa: PLR0913 since there are many options for these commands.


@app.command(
    name="codespell",
    help="Use the codespell spellchecker: detect common spelling mistakes.",
    rich_help_panel="Code Quality Tools",
)
def codespell(
    remove: bool = remove_opt,
    how: bool = how_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
    backend: BackendEnum = backend_opt,
) -> None:
    from usethis._config import usethis_config
    from usethis._config_file import files_manager
    from usethis._core.tool import use_codespell

    assert isinstance(backend, BackendEnum)

    with (
        usethis_config.set(
            offline=offline, quiet=quiet, frozen=frozen, backend=backend
        ),
        files_manager(),
    ):
        _run_tool(use_codespell, remove=remove, how=how)


@app.command(
    name="coverage.py",
    help="Use Coverage.py: a code coverage measurement tool.",
    rich_help_panel="Testing",
)
@app.command(
    name="coverage",
    help="Use Coverage.py: a code coverage measurement tool.",
    rich_help_panel="Testing",
    hidden=True,
    deprecated=True,
)
def coverage_py(
    remove: bool = remove_opt,
    how: bool = how_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
    backend: BackendEnum = backend_opt,
) -> None:
    from usethis._config import usethis_config
    from usethis._config_file import files_manager
    from usethis._core.tool import use_coverage_py

    assert isinstance(backend, BackendEnum)

    with (
        usethis_config.set(
            offline=offline, quiet=quiet, frozen=frozen, backend=backend
        ),
        files_manager(),
    ):
        _run_tool(use_coverage_py, remove=remove, how=how)


@app.command(
    name="deptry",
    help="Use the deptry linter: avoid missing or superfluous dependency declarations.",
    rich_help_panel="Code Quality Tools",
)
def deptry(
    remove: bool = remove_opt,
    how: bool = how_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
    backend: BackendEnum = backend_opt,
) -> None:
    from usethis._config import usethis_config
    from usethis._config_file import files_manager
    from usethis._core.tool import use_deptry

    assert isinstance(backend, BackendEnum)

    with (
        usethis_config.set(
            offline=offline, quiet=quiet, frozen=frozen, backend=backend
        ),
        files_manager(),
    ):
        _run_tool(use_deptry, remove=remove, how=how)


@app.command(
    name="import-linter",
    help="Use Import Linter: enforce a self-imposed architecture on imports.",
    rich_help_panel="Code Quality Tools",
)
def import_linter(
    remove: bool = remove_opt,
    how: bool = how_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
    backend: BackendEnum = backend_opt,
) -> None:
    from usethis._config import usethis_config
    from usethis._config_file import files_manager
    from usethis._core.tool import use_import_linter

    assert isinstance(backend, BackendEnum)

    with (
        usethis_config.set(
            offline=offline, quiet=quiet, frozen=frozen, backend=backend
        ),
        files_manager(),
    ):
        _run_tool(use_import_linter, remove=remove, how=how)


@app.command(
    name="pre-commit",
    help="Use the pre-commit framework to manage and maintain pre-commit hooks.",
    rich_help_panel="Code Quality Tools",
)
def pre_commit(
    remove: bool = remove_opt,
    how: bool = how_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
    backend: BackendEnum = backend_opt,
) -> None:
    from usethis._config import usethis_config
    from usethis._config_file import files_manager
    from usethis._core.tool import use_pre_commit

    assert isinstance(backend, BackendEnum)

    with (
        usethis_config.set(
            offline=offline, quiet=quiet, frozen=frozen, backend=backend
        ),
        files_manager(),
    ):
        _run_tool(use_pre_commit, remove=remove, how=how)


@app.command(
    name="pyproject-fmt",
    help="Use the pyproject-fmt linter: opinionated formatting of 'pyproject.toml' files.",
    rich_help_panel="Code Quality Tools",
)
def pyproject_fmt(
    remove: bool = remove_opt,
    how: bool = how_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
    backend: BackendEnum = backend_opt,
) -> None:
    from usethis._config import usethis_config
    from usethis._config_file import files_manager
    from usethis._core.tool import use_pyproject_fmt

    assert isinstance(backend, BackendEnum)

    with (
        usethis_config.set(
            offline=offline, quiet=quiet, frozen=frozen, backend=backend
        ),
        files_manager(),
    ):
        _run_tool(use_pyproject_fmt, remove=remove, how=how)


@app.command(
    name="pyproject.toml",
    help="Use a pyproject.toml file to configure the project.",
    rich_help_panel="Configuration Files",
)
def pyproject_toml(
    remove: bool = remove_opt,
    how: bool = how_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
    backend: BackendEnum = backend_opt,
) -> None:
    from usethis._config import usethis_config
    from usethis._config_file import files_manager
    from usethis._core.tool import use_pyproject_toml

    assert isinstance(backend, BackendEnum)

    with (
        usethis_config.set(
            offline=offline, quiet=quiet, frozen=frozen, backend=backend
        ),
        files_manager(),
    ):
        _run_tool(use_pyproject_toml, remove=remove, how=how)


@app.command(
    name="pytest", help="Use the pytest testing framework.", rich_help_panel="Testing"
)
def pytest(
    remove: bool = remove_opt,
    how: bool = how_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
    backend: BackendEnum = backend_opt,
) -> None:
    from usethis._config import usethis_config
    from usethis._config_file import files_manager
    from usethis._core.tool import use_pytest

    assert isinstance(backend, BackendEnum)

    with (
        usethis_config.set(
            offline=offline, quiet=quiet, frozen=frozen, backend=backend
        ),
        files_manager(),
    ):
        _run_tool(use_pytest, remove=remove, how=how)


@app.command(
    name="requirements.txt",
    help="Use a requirements.txt file exported from the uv lockfile.",
    rich_help_panel="Configuration Files",
)
def requirements_txt(
    remove: bool = remove_opt,
    how: bool = how_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
    backend: BackendEnum = backend_opt,
) -> None:
    from usethis._config import usethis_config
    from usethis._config_file import files_manager
    from usethis._core.tool import use_requirements_txt

    assert isinstance(backend, BackendEnum)

    with (
        usethis_config.set(
            offline=offline, quiet=quiet, frozen=frozen, backend=backend
        ),
        files_manager(),
    ):
        _run_tool(use_requirements_txt, remove=remove, how=how)


@app.command(
    name="ruff",
    help="Use Ruff: an extremely fast Python linter and code formatter.",
    rich_help_panel="Code Quality Tools",
)
def ruff(
    remove: bool = remove_opt,
    how: bool = how_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
    backend: BackendEnum = backend_opt,
    linter: bool = typer.Option(
        True,
        "--linter/--no-linter",
        help="Add or remove specifically the Ruff linter.",
    ),
    formatter: bool = typer.Option(
        True,
        "--formatter/--no-formatter",
        help="Add or remove specifically the Ruff formatter.",
    ),
) -> None:
    from usethis._config import usethis_config
    from usethis._config_file import files_manager
    from usethis._core.tool import use_ruff

    assert isinstance(backend, BackendEnum)

    with (
        usethis_config.set(
            offline=offline, quiet=quiet, frozen=frozen, backend=backend
        ),
        files_manager(),
    ):
        _run_tool(use_ruff, remove=remove, how=how, linter=linter, formatter=formatter)


def _run_tool(caller: UseToolFunc, *, remove: bool, how: bool, **kwargs: Any):
    from usethis._console import err_print
    from usethis.errors import UsethisError

    try:
        caller(remove=remove, how=how, **kwargs)
    except UsethisError as err:
        err_print(err)
        raise typer.Exit(code=1) from None


ALL_TOOL_COMMANDS: list[str] = [
    "codespell",
    "coverage.py",
    "deptry",
    "import-linter",
    "pre-commit",
    "pyproject.toml",
    "pyproject-fmt",
    "pytest",
    "requirements.txt",
    "ruff",
]
