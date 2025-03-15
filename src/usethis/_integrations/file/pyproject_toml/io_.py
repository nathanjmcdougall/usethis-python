from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from usethis._integrations.file.pyproject_toml.errors import (
    PyprojectTOMLDecodeError,
    PyprojectTOMLNotFoundError,
    PyprojectTOMLValueAlreadySetError,
    PyprojectTOMLValueMissingError,
    UnexpectedPyprojectTOMLIOError,
    UnexpectedPyprojectTOMLOpenError,
)
from usethis._integrations.file.toml.errors import (
    TOMLDecodeError,
    TOMLNotFoundError,
    TOMLValueAlreadySetError,
    TOMLValueMissingError,
    UnexpectedTOMLIOError,
    UnexpectedTOMLOpenError,
)
from usethis._integrations.file.toml.io_ import TOMLFileManager

if TYPE_CHECKING:
    from typing import Any

    from typing_extensions import Self


class PyprojectTOMLManager(TOMLFileManager):
    """Manages the pyproject.toml file."""

    @property
    def relative_path(self) -> Path:
        return Path("pyproject.toml")

    def __enter__(self) -> Self:
        try:
            return super().__enter__()
        except UnexpectedTOMLOpenError as err:
            raise UnexpectedPyprojectTOMLOpenError(err) from None

    def read_file(self) -> None:
        try:
            super().read_file()
        except TOMLNotFoundError as err:
            raise PyprojectTOMLNotFoundError(err) from None
        except UnexpectedTOMLIOError as err:
            raise UnexpectedPyprojectTOMLIOError(err) from None
        except TOMLDecodeError as err:
            raise PyprojectTOMLDecodeError(err) from None

    def _validate_lock(self) -> None:
        try:
            super()._validate_lock()
        except UnexpectedTOMLIOError as err:
            raise UnexpectedPyprojectTOMLIOError(err) from None

    def set_value(
        self, *, keys: list[str], value: Any, exists_ok: bool = False
    ) -> None:
        """Set a value in the pyproject.toml configuration file."""
        try:
            super().set_value(keys=keys, value=value, exists_ok=exists_ok)
        except TOMLValueAlreadySetError as err:
            raise PyprojectTOMLValueAlreadySetError(err) from None

    def remove_value(self, *, keys: list[str], missing_ok: bool = False) -> None:
        """Remove a value from the pyproject.toml configuration file."""
        try:
            super().remove_value(keys=keys, missing_ok=missing_ok)
        except TOMLValueMissingError as err:
            raise PyprojectTOMLValueMissingError(err) from None
