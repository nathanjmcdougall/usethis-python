from typing import Any

from pydantic import TypeAdapter, ValidationError

from usethis._integrations.pyproject_toml.errors import PyprojectTOMLProjectSectionError
from usethis._integrations.pyproject_toml.io_ import PyprojectTOMLManager


def get_project_dict() -> dict[str, Any]:
    pyproject = PyprojectTOMLManager().get().value

    try:
        project = TypeAdapter(dict).validate_python(pyproject["project"])
    except KeyError:
        msg = "The 'project' section is missing from 'pyproject.toml'."
        raise PyprojectTOMLProjectSectionError(msg) from None
    except ValidationError as err:
        msg = f"The 'project' section in 'pyproject.toml' is not a valid map: {err}"
        raise PyprojectTOMLProjectSectionError(msg) from None

    return project
