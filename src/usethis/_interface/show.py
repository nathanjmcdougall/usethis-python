import typer

from usethis._config import offline_opt, quiet_opt, usethis_config
from usethis._core.show import show_name

app = typer.Typer(help="Show information about the current project.")


@app.command(help="Show the name of the project")
def name(
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
) -> None:
    with usethis_config.set(offline=offline, quiet=quiet):
        show_name()