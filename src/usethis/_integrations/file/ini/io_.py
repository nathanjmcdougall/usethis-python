from __future__ import annotations

import configparser
from functools import singledispatch
from typing import TYPE_CHECKING

from configupdater import ConfigUpdater as INIDocument
from configupdater import Option, Section
from pydantic import TypeAdapter

from usethis._integrations.file.ini.errors import (
    INIDecodeError,
    ININestingError,
    ININotFoundError,
    INIValueAlreadySetError,
    INIValueMissingError,
    InvalidINITypeError,
    UnexpectedINIIOError,
    UnexpectedINIOpenError,
)
from usethis._io import (
    KeyValueFileManager,
    UnexpectedFileIOError,
    UnexpectedFileOpenError,
)

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, ClassVar

    from typing_extensions import Self


class INIFileManager(KeyValueFileManager):
    _content_by_path: ClassVar[dict[Path, INIDocument | None]] = {}

    def __enter__(self) -> Self:
        try:
            return super().__enter__()
        except UnexpectedFileOpenError as err:
            raise UnexpectedINIOpenError(err) from None

    def read_file(self) -> None:
        try:
            super().read_file()
        except FileNotFoundError as err:
            raise ININotFoundError(err) from None
        except UnexpectedFileIOError as err:
            raise UnexpectedINIIOError(err) from None
        except configparser.ParsingError as err:
            msg = f"Failed to decode '{self.name}': {err}"
            raise INIDecodeError(msg) from None

    def _dump_content(self) -> str:
        if self._content is None:
            msg = "Content is None, cannot dump."
            raise ValueError(msg)

        return str(self._content)

    def _parse_content(self, content: str) -> INIDocument:
        updater = INIDocument()
        updater.read_string(content)
        return updater

    def get(self) -> INIDocument:
        return super().get()

    def commit(self, document: INIDocument) -> None:
        return super().commit(document)

    @property
    def _content(self) -> INIDocument | None:
        return super()._content

    @_content.setter
    def _content(self, value: INIDocument | None) -> None:
        self._content_by_path[self.path] = value

    def _validate_lock(self) -> None:
        try:
            super()._validate_lock()
        except UnexpectedFileIOError as err:
            raise UnexpectedINIIOError(err) from None

    def __contains__(self, keys: list[str]) -> bool:
        """Check if the INI file contains a value at the given key.

        An non-existent file will return False.
        """
        try:
            root = self.get()
        except FileNotFoundError:
            return False

        if len(keys) == 0:
            # The root level exists if the file exists
            return True
        elif len(keys) == 1:
            (section_key,) = keys
            return section_key in root
        elif len(keys) == 2:
            section_key, option_key = keys
            try:
                return option_key in root[section_key]
            except KeyError:
                return False
        else:
            # Nested keys can't exist in INI files.
            return False

    def __getitem__(self, item: list[str]) -> Any:
        keys = item

        root = self.get()

        if len(keys) == 0:
            return _as_dict(root)
        elif len(keys) == 1:
            (section_key,) = keys
            return _as_dict(root[section_key])
        elif len(keys) == 2:
            (section_key, option_key) = keys
            return root[section_key][option_key].value
        else:
            msg = (
                f"INI files do not support nested config, whereas access to "
                f"'{self.name}' was attempted at '{'.'.join(keys)}'"
            )
            raise KeyError(msg)

    def set_value(
        self, *, keys: list[str], value: Any, exists_ok: bool = False
    ) -> None:
        """Set a value in the INI file.

        An empty list of keys corresponds to the root of the document.
        """
        root = self.get()

        if len(keys) == 0:
            self._set_value_in_root(root=root, value=value, exists_ok=exists_ok)
        elif len(keys) == 1:
            (section_key,) = keys
            self._set_value_in_section(
                root=root, section_key=keys[0], value=value, exists_ok=exists_ok
            )
        elif len(keys) == 2:
            (section_key, option_key) = keys
            self._set_value_in_option(
                root=root,
                section_key=section_key,
                option_key=option_key,
                value=value,
                exists_ok=exists_ok,
            )
        else:
            msg = (
                f"INI files do not support nested config, whereas access to "
                f"'{self.name}' was attempted at '{'.'.join(keys)}'"
            )
            raise ININestingError(msg)

        self.commit(root)

    @staticmethod
    def _set_value_in_root(
        root: INIDocument, value: dict[str, dict[str, str | list[str]]], exists_ok: bool
    ) -> None:
        root_dict = value

        if any(root) and not exists_ok:
            msg = "The INI file already has content at the root level"
            raise INIValueAlreadySetError(msg)

        # We need to remove section that are not in the new dict
        # We don't want to remove existing ones to keep their positions.
        for section_key in root.sections():
            if section_key not in root_dict:
                _remove_section(updater=root, section_key=section_key)

        TypeAdapter(dict).validate_python(root_dict)
        assert isinstance(root_dict, dict)

        for section_key, section_dict in root_dict.items():
            TypeAdapter(dict).validate_python(section_dict)
            assert isinstance(section_dict, dict)

            if section_key in root:
                for option_key in root[section_key]:
                    # We need to remove options that are not in the new dict
                    # We don't want to remove existing ones to keep their positions.
                    if option_key not in section_dict:
                        _remove_option(
                            updater=root, section_key=section_key, option_key=option_key
                        )
            else:
                root.add_section(section_key)

            for option_key, option in section_dict.items():
                INIFileManager._validated_set(
                    root=root,
                    section_key=section_key,
                    option_key=option_key,
                    value=option,
                )

    @staticmethod
    def _set_value_in_section(
        *,
        root: INIDocument,
        section_key: str,
        value: dict[str, str | list[str]],
        exists_ok: bool,
    ) -> None:
        TypeAdapter(dict).validate_python(value)
        assert isinstance(value, dict)

        section_dict = value

        if section_key in root:
            if not exists_ok:
                msg = f"The INI file already has content at the section '{section_key}'"
                raise INIValueAlreadySetError(msg)

            for option_key in root[section_key]:
                # We need to remove options that are not in the new dict
                # We don't want to remove existing ones to keep their positions.
                if option_key not in section_dict:
                    _remove_option(
                        updater=root, section_key=section_key, option_key=option_key
                    )

        for option_key, option in section_dict.items():
            INIFileManager._validated_set(
                root=root,
                section_key=section_key,
                option_key=option_key,
                value=option,
            )

    @staticmethod
    def _set_value_in_option(
        *,
        root: INIDocument,
        section_key: str,
        option_key: str,
        value: str,
        exists_ok: bool,
    ) -> None:
        if root.has_option(section=section_key, option=option_key) and not exists_ok:
            msg = (
                f"The INI file already has content at the section '{section_key}' "
                f"and option '{option_key}'"
            )
            raise INIValueAlreadySetError(msg)

        INIFileManager._validated_set(
            root=root, section_key=section_key, option_key=option_key, value=value
        )

    @staticmethod
    def _validated_set(
        *, root: INIDocument, section_key: str, option_key: str, value: str | list[str]
    ) -> None:
        if not isinstance(value, str | list):
            msg = (
                f"INI files only support strings (or lists of strings), but a "
                f"{type(value)} was provided."
            )
            raise InvalidINITypeError(msg)

        if section_key not in root:
            root.add_section(section_key)

        root.set(section=section_key, option=option_key, value=value)

    @staticmethod
    def _validated_append(
        *, root: INIDocument, section_key: str, option_key: str, value: str
    ) -> None:
        if not isinstance(value, str):
            msg = (
                f"INI files only support strings (or lists of strings), but a "
                f"{type(value)} was provided."
            )
            raise InvalidINITypeError(msg)

        if section_key not in root:
            root.add_section(section_key)

        if option_key not in root[section_key]:
            option = Option(key=option_key, value=value)
            root[section_key].add_option(option)
        else:
            root[section_key][option_key].append(value)

    def __delitem__(self, keys: list[str]) -> None:
        """Delete a value in the INI file.

        An empty list of keys corresponds to the root of the document.
        """
        root = self.get()

        if len(keys) == 0:
            removed = False
            for section_key in root.sections():
                removed |= _remove_section(updater=root, section_key=section_key)
        elif len(keys) == 1:
            (section_key,) = keys
            removed = _remove_section(updater=root, section_key=section_key)
        elif len(keys) == 2:
            section_key, option_key = keys
            removed = _remove_option(
                updater=root, section_key=section_key, option_key=option_key
            )

            # Cleanup section if empty
            if not root[section_key].options():
                _remove_section(updater=root, section_key=section_key)
        else:
            msg = (
                f"INI files do not support nested config, whereas access to "
                f"'{self.name}' was attempted at '{'.'.join(keys)}'"
            )
            raise INIValueMissingError(msg)

        if not removed:
            msg = f"INI file '{self.name}' does not contain the keys '{'.'.join(keys)}'"
            raise INIValueMissingError(msg)

        self.commit(root)

    def extend_list(self, *, keys: list[str], values: list[str]) -> None:
        """Extend a list in the INI file.

        An empty list of keys corresponds to the root of the document.
        """
        root = self.get()

        if len(keys) == 0:
            msg = (
                f"INI files do not support lists at the root level, whereas access to "
                f"'{self.name}' was attempted at '{'.'.join(keys)}'"
            )
            raise InvalidINITypeError(msg)
        elif len(keys) == 1:
            msg = (
                f"INI files do not support lists at the section level, whereas access "
                f"to '{self.name}' was attempted at '{'.'.join(keys)}'"
            )
            raise InvalidINITypeError(msg)
        elif len(keys) == 2:
            section_key, option_key = keys
            self._extend_list_in_option(
                root=root, section_key=section_key, option_key=option_key, values=values
            )
        else:
            msg = (
                f"INI files do not support nested config, whereas access to "
                f"'{self.name}' was attempted at '{'.'.join(keys)}'"
            )
            raise ININestingError(msg)

        self.commit(root)

    @staticmethod
    def _extend_list_in_option(
        *, root: INIDocument, section_key: str, option_key: str, values: list[str]
    ) -> None:
        for value in values:
            INIFileManager._validated_append(
                root=root, section_key=section_key, option_key=option_key, value=value
            )

    @staticmethod
    def _remove_from_list_in_option(
        *, root: INIDocument, section_key: str, option_key: str, values: list[str]
    ) -> None:
        if section_key not in root:
            return

        if option_key not in root[section_key]:
            return

        original_values = root[section_key][option_key].as_list()
        # If already not present, silently pass
        new_values = [value for value in original_values if value not in values]

        if len(new_values) == 0:
            # Remove the option if empty
            _remove_option(updater=root, section_key=section_key, option_key=option_key)

            # Remove the section if empty
            if not root[section_key].options():
                _remove_section(updater=root, section_key=section_key)

        elif len(new_values) == 1:
            # If only one value left, set it directly
            root[section_key][option_key] = new_values[0]
        elif len(new_values) > 1:
            root[section_key][option_key].set_values(new_values)

    def remove_from_list(self, *, keys: list[str], values: list[str]) -> None:
        """Remove values from a list in the INI file.

        An empty list of keys corresponds to the root of the document.
        """
        root = self.get()

        if len(keys) == 0:
            msg = (
                f"INI files do not support lists at the root level, whereas access to "
                f"'{self.name}' was attempted at '{'.'.join(keys)}'"
            )
            raise InvalidINITypeError(msg)
        elif len(keys) == 1:
            msg = (
                f"INI files do not support lists at the section level, whereas access "
                f"to '{self.name}' was attempted at '{'.'.join(keys)}'"
            )
            raise InvalidINITypeError(msg)
        elif len(keys) == 2:
            section_key, option_key = keys
            self._remove_from_list_in_option(
                root=root, section_key=section_key, option_key=option_key, values=values
            )
        else:
            msg = (
                f"INI files do not support nested config, whereas access to "
                f"'{self.name}' was attempted at '{'.'.join(keys)}'"
            )
            raise ININestingError(msg)

        self.commit(root)


@singledispatch
def _as_dict(
    value: INIDocument | Section,
) -> dict[str, dict[str, Any]] | dict[str, Any]:
    raise NotImplementedError


@_as_dict.register(INIDocument)
def _(value: INIDocument) -> dict[str, dict[str, Any]]:
    return {k: _as_dict(v) for k, v in value.items()}


@_as_dict.register(Section)
def _(value: Section) -> dict[str, Any]:
    return {option.key: option.value for option in value.iter_options()}


def _remove_option(updater: INIDocument, section_key: str, option_key: str) -> bool:
    try:
        return updater.remove_option(section=section_key, option=option_key)
    except configparser.NoSectionError as err:
        raise INIValueMissingError(err) from None


def _remove_section(updater: INIDocument, section_key: str) -> bool:
    return updater.remove_section(name=section_key)
