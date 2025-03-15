from __future__ import annotations

from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Generic, TypeVar

from usethis.errors import UsethisError

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Any, ClassVar

    from typing_extensions import Self

DocumentT = TypeVar("DocumentT")


class UnexpectedFileOpenError(UsethisError):
    """Raised when a file is unexpectedly opened."""


class UnexpectedFileIOError(UsethisError, IOError):
    """Raised when an unexpected attempt is made to read or write the pyproject.toml file."""


class UsethisFileManager(Generic[DocumentT]):
    """Manages file access with deferred writes using a context manager.

    This class implements the Command Pattern, encapsulating file operations. It defers
    writing changes to the file until the context is exited, ensuring that file I/O
    operations are performed efficiently and only when necessary.
    """

    # https://github.com/python/mypy/issues/5144
    # The Any in this expression should be identified with DocumentT
    _content_by_path: ClassVar[dict[Path, Any | None]] = {}

    @property
    @abstractmethod
    def relative_path(self) -> Path:
        """Return the relative path to the file."""
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self.relative_path.name

    def __init__(self) -> None:
        self.path = (Path.cwd() / self.relative_path).resolve()

    def __enter__(self) -> Self:
        if self.is_locked():
            msg = (
                f"The '{self.name}' file is already in use by another instance of "
                f"'{self.__class__.__name__}'."
            )
            raise UnexpectedFileOpenError(msg)

        self.lock()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if not self.is_locked():
            # This could happen if we decide to delete the file.
            return

        self.write_file()
        self.unlock()

    def get(self) -> DocumentT:
        """Retrieve the document, reading from disk if necessary."""
        self._validate_lock()

        if self._content is None:
            self.read_file()
            assert self._content is not None

        return self._content

    def commit(self, document: DocumentT) -> None:
        """Store the given document in memory for deferred writing."""
        self._validate_lock()
        self._content = document

    def write_file(self) -> None:
        """Write the stored document to disk if there are changes."""
        self._validate_lock()

        if self._content is None:
            # No changes made, nothing to write.
            return

        self.path.write_text(self._dump_content())

    def read_file(self) -> None:
        """Read the document from disk and store it in memory."""
        self._validate_lock()

        if self._content is not None:
            msg = (
                f"The '{self.name}' file has already been read, use 'get()' to "
                f"access the content."
            )
            raise UnexpectedFileIOError(msg)
        try:
            self._content = self._parse_content(self.path.read_text())
        except FileNotFoundError:
            msg = f"'{self.name}' not found in the current directory at '{self.path}'"
            raise FileNotFoundError(msg) from None

    @abstractmethod
    def _dump_content(self) -> str:
        """Return the content of the document as a string."""
        raise NotImplementedError

    @abstractmethod
    def _parse_content(self, content: str) -> DocumentT:
        """Parse the content of the document."""
        raise NotImplementedError

    @property
    def _content(self) -> DocumentT | None:
        return self._content_by_path.get(self.path)

    @_content.setter
    def _content(self, value: DocumentT | None) -> None:
        self._content_by_path[self.path] = value

    def _validate_lock(self) -> None:
        if not self.is_locked():
            msg = (
                f"The '{self.name}' file has not been opened yet. Please enter the "
                f"context manager, e.g. 'with {self.__class__.__name__}():'"
            )
            raise UnexpectedFileIOError(msg)

    def is_locked(self) -> bool:
        return self.path in self._content_by_path

    def lock(self) -> None:
        self._content = None

    def unlock(self) -> None:
        self._content_by_path.pop(self.path, None)


class KeyValueFileManager(UsethisFileManager, Generic[DocumentT]):
    """A manager for files which store (at least some) values in key-value mappings."""

    @abstractmethod
    def do_keys_exist(
        self, keys: list[str]
    ) -> bool:  # TODO this should be __contains__ or similar
        """Check if the given ID keys exist in the configuration file."""
        raise NotImplementedError

    @abstractmethod
    def __getitem__(self, item: list[str]) -> Any:
        raise NotImplementedError

    @abstractmethod
    def set_value(  # TODO naming. Could this be __setitem__ , but how to handle the exists_ok cases?
        self, *, keys: list[str], value: Any, exists_ok: bool = False
    ) -> None:
        """Set a value in the configuration file."""
        raise NotImplementedError

    @abstractmethod  # TODO naming. Could this be __delitem__ , but how to handle the missing_ok cases?
    def remove_value(self, *, keys: list[str], missing_ok: bool = False) -> None:
        """Remove a value from the configuration file."""
        raise NotImplementedError

    @abstractmethod
    def extend_list(
        self, *, keys: list[str], values: list[Any]
    ) -> None:  # TODO id_keys naming vs keys
        """Extend a list in the configuration file."""
        raise NotImplementedError

    @abstractmethod
    def remove_from_list(
        self, *, keys: list[str], values: list[Any]
    ) -> None:  # TODO id_keys naming vs keys
        """Remove values from a list in the configuration file."""
        raise NotImplementedError
