from usethis.errors import UsethisError


class PyProjectTOMLError(UsethisError):
    """Raised when aspects of 'pyproject.toml' are missing, invalid, or unexpected."""


class PyProjectTOMLNotFoundError(PyProjectTOMLError, FileNotFoundError):
    """Raised when a pyproject.toml file is not found."""


class PyProjectTOMLDecodeError(PyProjectTOMLError):
    """Raised when a pyproject.toml file cannot be decoded."""


class PyProjectTOMLProjectNameError(PyProjectTOMLError):
    """Raised when the 'project.name' key is missing or invalid in 'pyproject.toml'."""


class PyProjectTOMLProjectSectionError(PyProjectTOMLError):
    """Raised when the 'project' section is missing or invalid in 'pyproject.toml'."""


class PyProjectTOMLValueAlreadySetError(PyProjectTOMLError):
    """Raised when a value is unexpectedly already set in the 'pyproject.toml' file."""


class PyPorjectTOMLValueMIssingError(PyProjectTOMLError):
    """Raised when a value is unexpectedly missing from the 'pyproject.toml' file."""
