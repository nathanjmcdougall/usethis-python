from __future__ import annotations

import typer

from usethis._options import backend_opt, quiet_opt
from usethis._types.backend import BackendEnum
from usethis._types.status import DevelopmentStatusEnum


def status(
    status: DevelopmentStatusEnum = typer.Argument(
        default=..., help="Docstring style to enforce."
    ),
    quiet: bool = quiet_opt,
    backend_opt: BackendEnum = backend_opt,
) -> None:
    from usethis._config import usethis_config
    from usethis._config_file import files_manager
    from usethis._console import err_print
    from usethis._core.status import use_development_status
    from usethis.errors import UsethisError

    assert isinstance(status, DevelopmentStatusEnum)
    assert isinstance(backend_opt, BackendEnum)

    with usethis_config.set(quiet=quiet), files_manager():
        try:
            use_development_status(status)
        except UsethisError as err:
            err_print(err)
            raise typer.Exit(code=1) from None
