import typer

from usethis._config import offline_opt, quiet_opt, usethis_config
from usethis._core.badge import (
    add_badge,
    get_pre_commit_badge,
    get_pypi_badge,
    get_ruff_badge,
    remove_badge,
)
from usethis._integrations.pyproject_toml.io_ import PyprojectTOMLManager

app = typer.Typer(help="Add badges to the top of the README.md file.")

remove_opt = typer.Option(
    False, "--remove", help="Remove the badge instead of adding it."
)


@app.command(help="Add a badge with the version of your package on PyPI.")
def pypi(
    remove: bool = remove_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
) -> None:
    with (
        usethis_config.set(offline=offline, quiet=quiet),
        PyprojectTOMLManager(),
    ):
        if not remove:
            add_badge(get_pypi_badge())
        else:
            remove_badge(get_pypi_badge())


@app.command(help="Add a badge for the Ruff linter.")
def ruff(
    remove: bool = remove_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
) -> None:
    with (
        usethis_config.set(offline=offline, quiet=quiet),
        PyprojectTOMLManager(),
    ):
        if not remove:
            add_badge(get_ruff_badge())
        else:
            remove_badge(get_ruff_badge())


@app.command(help="Add a badge for the pre-commit framework.")
def pre_commit(
    remove: bool = remove_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
) -> None:
    with (
        usethis_config.set(offline=offline, quiet=quiet),
        PyprojectTOMLManager(),
    ):
        if not remove:
            add_badge(get_pre_commit_badge())
        else:
            remove_badge(get_pre_commit_badge())
