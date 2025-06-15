from __future__ import annotations

import typer

from usethis._config import quiet_opt, usethis_config
from usethis._config_file import files_manager
from usethis._console import err_print
from usethis._core.docstyle import DocStyleEnum, use_docstyle
from usethis.errors import UsethisError


def docstyle(
    style: DocStyleEnum = typer.Argument(
        default="google", help="Docstring style to enforce."
    ),
    quiet: bool = quiet_opt,
) -> None:
    assert isinstance(style, DocStyleEnum)

    with usethis_config.set(quiet=quiet), files_manager():
        try:
            use_docstyle(style)
        except UsethisError as err:
            err_print(err)
            raise typer.Exit(code=1) from None
