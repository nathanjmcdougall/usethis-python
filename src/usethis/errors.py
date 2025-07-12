"""Custom errors for the usethis package."""

from __future__ import annotations


class UsethisError(Exception):
    """Base class for all errors."""


class FileConfigError(UsethisError):
    """Raised when there is an error in a file configuration."""

    @property
    def name(self) -> str:
        """The name of the file that has a configuration error.

        This is not necessarily defined for all subclasses, and will raise
        NotImplementedError if not overridden.
        """
        raise NotImplementedError


class FileDecodeError(FileConfigError):
    """Raised when a file is unexpectedly not decodable."""

    @property
    def name(self) -> str:
        """The name of the file that could not be decoded.

        This is not necessarily defined for all subclasses, and will raise
        NotImplementedError if not overridden.
        """
        raise NotImplementedError


class ForbiddenBackendError(UsethisError):
    """Raised when an unexpected attempt to use a particular backend.

    For example, when the uv backend is not enabled but a uv subprocess is invoked.
    """


class DepGroupError(UsethisError):
    """Raised when adding or removing a dependency from a group fails."""
