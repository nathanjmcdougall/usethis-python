import typer

from usethis._config import offline_opt, quiet_opt, usethis_config
from usethis._console import err_print, info_print
from usethis._core.ci import use_ci_bitbucket
from usethis._integrations.pyproject_toml.io_ import PyprojectTOMLManager
from usethis.errors import UsethisError

app = typer.Typer(help="Add config for Continuous Integration (CI) pipelines.")


@app.command(help="Use Bitbucket pipelines for CI.")
def bitbucket(
    remove: bool = typer.Option(
        False, "--remove", help="Remove Bitbucket pipelines CI instead of adding it."
    ),
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
) -> None:
    try:
        with (
            usethis_config.set(offline=offline, quiet=quiet),
            PyprojectTOMLManager(),
        ):
            use_ci_bitbucket(remove=remove)
    except UsethisError as err:
        err_print(err)

        if "mapping values are not allowed here" in str(err):
            info_print("Hint: You may have incorrect indentation the YAML file.")
        raise typer.Exit(code=1) from None
