from usethis.errors import UsethisError


class UVError(UsethisError):
    """Base class for exceptions relating to uv."""


class UVDepGroupError(UVError):
    """Raised when adding or removing a dependency from a group fails."""


class UVSubprocessFailedError(UVError):
    """Raised when a subprocess call to uv fails."""