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


def lint(  # noqa: PLR0913
    remove: bool = remove_opt,
    how: bool = how_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
    backend: BackendEnum = backend_opt,
) -> None:
    """Add recommended linters to the project."""
    from usethis._config import usethis_config
    from usethis._config_file import files_manager
    from usethis._console import err_print
    from usethis._toolset.lint import use_linters
    from usethis.errors import UsethisError

    assert isinstance(backend, BackendEnum)

    with (
        usethis_config.set(
            offline=offline, quiet=quiet, frozen=frozen, backend=backend
        ),
        files_manager(),
    ):
        try:
            use_linters(remove=remove, how=how)
        except UsethisError as err:
            err_print(err)
            raise typer.Exit(code=1) from None
