from __future__ import annotations

from usethis.errors import DepGroupError, UsethisError


class UVError(UsethisError):
    """Base class for exceptions relating to uv."""


class UVDepGroupError(DepGroupError):
    """Raised when adding or removing a dependency from a group fails."""


class UVSubprocessFailedError(UVError):
    """Raised when a subprocess call to uv fails."""


class UVInitError(UVSubprocessFailedError):
    """Raised when the uv init command fails to create a pyproject.toml file."""


class UVUnparsedPythonVersionError(UVError):
    """Raised when a Python version string cannot be parsed."""
