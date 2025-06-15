from __future__ import annotations

from typing import TYPE_CHECKING

from usethis._config import usethis_config
from usethis._console import box_print, tick_print, warn_print
from usethis._integrations.file.pyproject_toml.errors import PyprojectTOMLError
from usethis._integrations.file.pyproject_toml.name import get_description
from usethis._integrations.project.name import get_project_name
from usethis.errors import UsethisError

if TYPE_CHECKING:
    from pathlib import Path


def add_readme() -> None:
    """Add a README.md file to the project."""
    # Any file extension is fine, but we'll use '.md' for consistency.

    try:
        path = get_readme_path()
    except FileNotFoundError:
        pass
    else:
        # Check if the file is non-empty; if so, we will exit early
        existing_content = path.read_text().strip()
        if existing_content:
            return

    project_name = get_project_name()

    try:
        project_description = get_description()
    except PyprojectTOMLError:
        project_description = None

    if project_name is not None and project_description is not None:
        content = f"""\
# {project_name}

{project_description}
"""
    elif project_name is not None:
        content = f"""\
# {project_name}
"""
    elif project_description is not None:
        content = f"""\
{project_description}
"""
    else:
        content = ""

    tick_print("Writing 'README.md'.")
    (usethis_config.cpd() / "README.md").write_text(content, encoding="utf-8")
    box_print("Populate 'README.md' to help users understand the project.")


def get_readme_path():
    path_readme_md = usethis_config.cpd() / "README.md"
    path_readme = usethis_config.cpd() / "README"

    if path_readme_md.exists() and path_readme_md.is_file():
        return path_readme_md
    elif path_readme.exists() and path_readme.is_file():
        return path_readme

    for path in usethis_config.cpd().glob("README*"):
        if path.is_file() and path.stem == "README":
            return path

    msg = "No README file found."
    raise FileNotFoundError(msg)


class NonMarkdownREADMEError(UsethisError):
    """Raised when the README file is not Markdown based on its extension."""


def get_markdown_readme_path() -> Path:
    path = get_readme_path()

    if path.name == "README.md":
        pass
    elif path.name == "README":
        warn_print("Assuming 'README' file is Markdown.")
    else:
        msg = f"README file '{path.name}' is not Markdown based on its extension."
        raise NonMarkdownREADMEError(msg)

    return path


def is_readme_used():
    """Check if the README.md file is used."""
    try:
        get_readme_path()
    except FileNotFoundError:
        return False

    return True
