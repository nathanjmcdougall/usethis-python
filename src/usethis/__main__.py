import typer

import usethis._interface.badge
import usethis._interface.browse
import usethis._interface.ci
import usethis._interface.show
import usethis._interface.tool
from usethis._config import quiet_opt, usethis_config
from usethis._core.readme import add_readme

app = typer.Typer(
    help=(
        "Automate Python package and project setup tasks that are otherwise "
        "performed manually."
    )
)
app.add_typer(usethis._interface.badge.app, name="badge")
app.add_typer(usethis._interface.browse.app, name="browse")
app.add_typer(usethis._interface.ci.app, name="ci")
app.add_typer(usethis._interface.show.app, name="show")
app.add_typer(usethis._interface.tool.app, name="tool")


@app.command(help="Add a README.md file to the project.")
def readme(
    quiet: bool = quiet_opt,
) -> None:
    with usethis_config.set(quiet=quiet):
        add_readme()


app(prog_name="usethis")


__all__ = ["app"]
