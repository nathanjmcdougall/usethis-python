from usethis._integrations.backend.uv.init import ensure_pyproject_toml
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager


def add_author(
    *,
    # Strictly, a name is not required by the TOML spec, but we do require it
    name: str,
    email: str | None = None,
    overwrite: bool = False,
):
    ensure_pyproject_toml(author=False)

    if email is not None:
        values = [{"name": name, "email": email}]
    else:
        values = [{"name": name}]

    if not overwrite:
        PyprojectTOMLManager().extend_list(
            keys=["project", "authors"],
            values=values,
        )

        # Moving the authors list to the end of the project table to avoid a bug in tomlkit
        # Suspected to be similar to this https://github.com/python-poetry/tomlkit/issues/381
        full = PyprojectTOMLManager()[["project", "authors"]]
        del PyprojectTOMLManager()[["project", "authors"]]
        PyprojectTOMLManager()[["project", "authors"]] = full
    else:
        PyprojectTOMLManager()[["project", "authors"]] = values
