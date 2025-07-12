from __future__ import annotations

import typer

from usethis._options import backend_opt, quiet_opt
from usethis._types.backend import BackendEnum


def author(
    name: str = typer.Option(..., "--name", help="Author name"),
    email: str = typer.Option("", "--email", help="Author email"),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite any existing authors"
    ),
    quiet: bool = quiet_opt,
    backend: BackendEnum = backend_opt,
) -> None:
    from usethis._config import usethis_config
    from usethis._config_file import files_manager
    from usethis._console import err_print
    from usethis._core.author import add_author
    from usethis.errors import UsethisError

    assert isinstance(backend, BackendEnum)

    if not email:
        email_arg = None
    else:
        email_arg = email

    with usethis_config.set(quiet=quiet), files_manager():
        try:
            add_author(name=name, email=email_arg, overwrite=overwrite)
        except UsethisError as err:
            err_print(err)
            raise typer.Exit(code=1) from None
