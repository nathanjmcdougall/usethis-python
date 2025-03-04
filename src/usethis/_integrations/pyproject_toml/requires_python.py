from packaging.specifiers import SpecifierSet
from pydantic import TypeAdapter

from usethis._integrations.pyproject_toml.io_ import PyprojectTOMLManager


class MissingRequiresPythonError(Exception):
    """Raised when the 'requires-python' key is missing."""


def get_requires_python() -> SpecifierSet:
    pyproject = PyprojectTOMLManager().get()

    try:
        requires_python = TypeAdapter(str).validate_python(
            TypeAdapter(dict).validate_python(pyproject["project"])["requires-python"]
        )
    except KeyError:
        msg = "The 'project.requires-python' value is missing from 'pyproject.toml'."
        raise MissingRequiresPythonError(msg) from None

    return SpecifierSet(requires_python)
