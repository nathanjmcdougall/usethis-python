import typer

from usethis._options import backend_opt, offline_opt, quiet_opt
from usethis._types.backend import BackendEnum

remove_opt = typer.Option(
    False, "--remove", help="Remove the rule selection or ignore status."
)
ignore_opt = typer.Option(
    False, "--ignore", help="Add (or remove) the rule to (or from) the ignore list"
)


def rule(  # noqa: PLR0913
    rules: list[str],
    remove: bool = remove_opt,
    ignore: bool = ignore_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    backend: BackendEnum = backend_opt,
) -> None:
    from usethis._config import usethis_config
    from usethis._config_file import files_manager
    from usethis._console import err_print
    from usethis._core.rule import (
        deselect_rules,
        ignore_rules,
        select_rules,
        unignore_rules,
    )
    from usethis.errors import UsethisError

    assert isinstance(backend, BackendEnum)

    with (
        usethis_config.set(offline=offline, quiet=quiet, backend=backend),
        files_manager(),
    ):
        try:
            if remove and not ignore:
                deselect_rules(rules)
            elif ignore and not remove:
                ignore_rules(rules)
            elif remove and ignore:
                unignore_rules(rules)
            else:
                select_rules(rules)
        except UsethisError as err:
            err_print(err)
            raise typer.Exit(code=1) from None
