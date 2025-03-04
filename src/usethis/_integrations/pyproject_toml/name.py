from pydantic import TypeAdapter, ValidationError

from usethis._integrations.pyproject_toml.errors import (
    PyprojectTOMLProjectDescriptionError,
    PyprojectTOMLProjectNameError,
)
from usethis._integrations.pyproject_toml.project import get_project_dict


def get_name() -> str:
    project_dict = get_project_dict()

    try:
        name = TypeAdapter(str).validate_python(project_dict["name"])
    except KeyError:
        msg = "The 'project.name' value is missing from 'pyproject.toml'."
        raise PyprojectTOMLProjectNameError(msg) from None
    except ValidationError as err:
        msg = (
            f"The 'project.name' value in 'pyproject.toml' is not a valid string: {err}"
        )
        raise PyprojectTOMLProjectNameError(msg) from None

    return name


def get_description() -> str:
    project_dict = get_project_dict()

    try:
        description = TypeAdapter(str).validate_python(project_dict["description"])
    except KeyError:
        msg = "The 'project.description' value is missing from 'pyproject.toml'."
        raise PyprojectTOMLProjectDescriptionError(msg) from None
    except ValidationError as err:
        msg = f"The 'project.description' value in 'pyproject.toml' is not a valid string: {err}"
        raise PyprojectTOMLProjectDescriptionError(msg) from None

    return description
