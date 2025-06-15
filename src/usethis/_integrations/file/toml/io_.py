from __future__ import annotations

import contextlib
import copy
import re
from typing import TYPE_CHECKING, Any

import mergedeep
import tomlkit.api
import tomlkit.items
from pydantic import TypeAdapter
from tomlkit import TOMLDocument
from tomlkit.container import OutOfOrderTableProxy
from tomlkit.exceptions import TOMLKitError
from typing_extensions import assert_never

from usethis._integrations.file.toml.errors import (
    TOMLDecodeError,
    TOMLNotFoundError,
    TOMLValueAlreadySetError,
    TOMLValueMissingError,
    UnexpectedTOMLIOError,
    UnexpectedTOMLOpenError,
)
from usethis._io import (
    Key,
    KeyValueFileManager,
    UnexpectedFileIOError,
    UnexpectedFileOpenError,
    print_keys,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path
    from typing import ClassVar

    from tomlkit.container import Container
    from tomlkit.items import Item
    from typing_extensions import Never, Self

    from usethis._io import Key


class TOMLFileManager(KeyValueFileManager):
    """An abstract class for managing TOML files."""

    _content_by_path: ClassVar[dict[Path, TOMLDocument | None]] = {}

    def __enter__(self) -> Self:
        try:
            return super().__enter__()
        except UnexpectedFileOpenError as err:
            raise UnexpectedTOMLOpenError(err) from None

    def read_file(self) -> None:
        try:
            super().read_file()
        except FileNotFoundError as err:
            raise TOMLNotFoundError(err) from None
        except UnexpectedFileIOError as err:
            raise UnexpectedTOMLIOError(err) from None
        except TOMLKitError as err:
            msg = f"Failed to decode '{self.name}': {err}"
            raise TOMLDecodeError(msg) from None

    def _dump_content(self) -> str:
        if self._content is None:
            msg = "Content is None, cannot dump."
            raise ValueError(msg)

        return tomlkit.api.dumps(self._content)

    def _parse_content(self, content: str) -> TOMLDocument:
        return tomlkit.api.parse(content)

    def get(self) -> TOMLDocument:
        return super().get()

    def commit(self, document: TOMLDocument) -> None:
        return super().commit(document)

    @property
    def _content(self) -> TOMLDocument | None:
        return super()._content

    @_content.setter
    def _content(self, value: TOMLDocument | None) -> None:
        self._content_by_path[self.path] = value

    def _validate_lock(self) -> None:
        try:
            super()._validate_lock()
        except UnexpectedFileIOError as err:
            raise UnexpectedTOMLIOError(err) from None

    def __contains__(self, keys: Sequence[Key]) -> bool:
        """Check if the TOML file contains a value.

        An non-existent file will return False.
        """
        keys = _validate_keys(keys)
        try:
            try:
                container = self.get()
            except FileNotFoundError:
                return False
            for key in keys:
                TypeAdapter(dict).validate_python(container)
                assert isinstance(container, dict)
                container = container[key]
        except KeyError:
            return False

        return True

    def __getitem__(self, item: Sequence[Key]) -> Any:
        keys = item
        keys = _validate_keys(keys)

        d = self.get()
        for key in keys:
            TypeAdapter(dict).validate_python(d)
            assert isinstance(d, dict)
            d = d[key]

        return d

    def set_value(
        self, *, keys: Sequence[Key], value: Any, exists_ok: bool = False
    ) -> None:
        """Set a value in the TOML file.

        An empty list of keys corresponds to the root of the document.
        """
        toml_document = copy.copy(self.get())
        keys = _validate_keys(keys)

        if not keys:
            # Root level config - value must be a mapping.
            TypeAdapter(dict).validate_python(toml_document)
            assert isinstance(toml_document, dict)
            TypeAdapter(dict).validate_python(value)
            assert isinstance(value, dict)
            if not toml_document or exists_ok:
                toml_document.update(value)
                self.commit(toml_document)
                return

        d, parent = toml_document, {}
        shared_keys: list[str] = []
        try:
            # Index our way into each ID key.
            # Eventually, we should land at a final dict, which is the one we are setting.
            for key in keys:
                TypeAdapter(dict).validate_python(d)
                assert isinstance(d, dict)
                d, parent = d[key], d
                shared_keys.append(key)
        except KeyError:
            _set_value_in_existing(
                toml_document=toml_document,
                current_container=d,
                keys=keys,
                current_keys=shared_keys,
                value=value,
            )
        else:
            if not exists_ok:
                # The configuration is already present, which is not allowed.
                _raise_already_set(keys)
            else:
                # The configuration is already present, but we're allowed to overwrite it.
                TypeAdapter(dict).validate_python(parent)
                assert isinstance(parent, dict)
                parent[keys[-1]] = value

        self.commit(toml_document)  # type: ignore[reportAssignmentType]

    def __delitem__(self, keys: Sequence[Key]) -> None:
        """Delete a value in the TOML file.

        An empty list of keys corresponds to the root of the document.

        Trying to delete a key from a document that doesn't exist will pass silently.
        """
        try:
            toml_document = copy.copy(self.get())
        except FileNotFoundError:
            return
        keys = _validate_keys(keys)

        # Exit early if the configuration is not present.
        try:
            d = toml_document
            for key in keys:
                TypeAdapter(dict).validate_python(d)
                assert isinstance(d, dict)
                d = d[key]
        except KeyError:
            # N.B. by convention a del call should raise an error if the key is not found.
            msg = f"Configuration value '{print_keys(keys)}' is missing."
            raise TOMLValueMissingError(msg) from None

        # Remove the configuration.
        d = toml_document
        for key in keys[:-1]:
            TypeAdapter(dict).validate_python(d)
            assert isinstance(d, dict)
            d = d[key]
        assert isinstance(d, dict)
        if not keys:
            # i.e. the case where we're deleting the root of the document.
            for key in list(d.keys()):
                del d[key]
        else:
            with contextlib.suppress(KeyError):
                # N.B. There was a strange behaviour (bug?) in tomlkit where deleting a
                # key has two separate lines:
                # self._value.remove(key)  # noqa: ERA001
                # dict.__delitem__(self, key)  # noqa: ERA001
                # but it's not clear why there's this duplicate and it causes a KeyError
                # in some cases.
                if isinstance(d, OutOfOrderTableProxy):
                    # N.B. this case isn't expected based on the type annotations but
                    # it is possible in practice.
                    d.__delitem__(keys[-1])
                else:
                    d.remove(keys[-1])

            # Cleanup: any empty sections should be removed.
            for idx in range(len(keys) - 1):
                d, parent = toml_document, {}

                for key in keys[: idx + 1]:
                    d, parent = d[key], d
                    TypeAdapter(dict).validate_python(d)
                    TypeAdapter(dict).validate_python(parent)
                    assert isinstance(d, dict)
                    assert isinstance(parent, dict)
                assert isinstance(d, dict)
                if not d:
                    del parent[keys[idx]]

        self.commit(toml_document)

    def extend_list(self, *, keys: Sequence[Key], values: list[Any]) -> None:
        if not keys:
            msg = "At least one ID key must be provided."
            raise ValueError(msg)
        keys = _validate_keys(keys)

        toml_document = copy.copy(self.get())

        try:
            d = toml_document
            for key in keys[:-1]:
                TypeAdapter(dict).validate_python(d)
                assert isinstance(d, dict)
                d = d[key]
            p_parent = d
            TypeAdapter(dict).validate_python(p_parent)
            assert isinstance(p_parent, dict)
            d = p_parent[keys[-1]]
        except KeyError:
            contents = values
            for key in reversed(keys):
                contents = {key: contents}
            assert isinstance(contents, dict)
            toml_document = mergedeep.merge(toml_document, contents)
            assert isinstance(toml_document, TOMLDocument)
        else:
            TypeAdapter(dict).validate_python(p_parent)
            TypeAdapter(list).validate_python(d)
            assert isinstance(p_parent, dict)
            assert isinstance(d, list)
            p_parent[keys[-1]] = d + values

        self.commit(toml_document)

    def remove_from_list(self, *, keys: Sequence[Key], values: list[Any]) -> None:
        if not keys:
            msg = "At least one ID key must be provided."
            raise ValueError(msg)
        keys = _validate_keys(keys)

        toml_document = copy.copy(self.get())

        try:
            p = toml_document
            for key in keys[:-1]:
                TypeAdapter(dict).validate_python(p)
                assert isinstance(p, dict)
                p = p[key]

            p_parent = p
            TypeAdapter(dict).validate_python(p_parent)
            assert isinstance(p_parent, dict)
            p = p_parent[keys[-1]]
        except KeyError:
            # The configuration is not present - do not modify
            return

        TypeAdapter(dict).validate_python(p_parent)
        TypeAdapter(list).validate_python(p)
        assert isinstance(p_parent, dict)
        assert isinstance(p, list)

        new_values = [value for value in p if value not in values]
        p_parent[keys[-1]] = new_values

        self.commit(toml_document)


def _set_value_in_existing(
    *,
    toml_document: TOMLDocument,
    current_container: TOMLDocument | Item | Container,
    keys: Sequence[Key],
    current_keys: Sequence[Key],
    value: Any,
) -> None:
    # The old configuration should be kept for all ID keys except the
    # final/deepest one which shouldn't exist anyway since we checked as much,
    # above. For example, if there is [tool.ruff] then we shouldn't overwrite it
    # with [tool.deptry]; they should coexist. So under the "tool" key, we need
    # to "merge" the two dicts.

    if len(keys) <= 3:
        contents = value
        for key in reversed(keys):
            contents = {key: contents}
        toml_document = mergedeep.merge(toml_document, contents)  # type: ignore[reportAssignmentType]
        assert isinstance(toml_document, TOMLDocument)
    else:
        # Note that this alternative logic is just to avoid a bug:
        # https://github.com/usethis-python/usethis-python/issues/507
        TypeAdapter(dict).validate_python(current_container)
        assert isinstance(current_container, dict)

        unshared_keys = keys[len(current_keys) :]

        if len(current_keys) == 1:
            # In this case, we need to "seed" the section to avoid another bug:
            # https://github.com/usethis-python/usethis-python/issues/558

            placeholder = {keys[0]: {keys[1]: {}}}
            toml_document = mergedeep.merge(toml_document, placeholder)  # type: ignore[reportArgumentType]

            contents = value
            for key in reversed(unshared_keys[1:]):
                contents = {key: contents}

            current_container[keys[1]] = contents  # type: ignore[reportAssignmentType]
        else:
            current_container[_get_unified_key(unshared_keys)] = value


def _validate_keys(keys: Sequence[Key]) -> list[str]:
    """Validate the keys.

    Args:
        keys: The keys to validate.

    Raises:
        ValueError: If the keys are not valid.
    """
    so_far_keys: list[str] = []
    for key in keys:
        if isinstance(key, str):
            so_far_keys.append(key)
        elif isinstance(key, re.Pattern):
            # Currently no need for this, perhaps we may add it in the future.
            msg = (
                f"Regex-based keys are not currently supported in TOML files: "
                f"{print_keys([*so_far_keys, key])}"
            )
            raise NotImplementedError(msg)
        else:
            assert_never(key)

    return so_far_keys


def _raise_already_set(keys: Sequence[Key]) -> Never:
    """Raise an error if the configuration is already set."""
    if keys:
        msg = f"Configuration value '{print_keys(keys)}' is already set."
    else:
        msg = "Configuration value at root level is already set."
    raise TOMLValueAlreadySetError(msg)


def _get_unified_key(keys: Sequence[Key]) -> tomlkit.items.Key:
    keys = _validate_keys(keys)

    single_keys = [tomlkit.items.SingleKey(key) for key in keys]
    if len(single_keys) == 1:
        (unified_key,) = single_keys
    else:
        unified_key = tomlkit.items.DottedKey(single_keys)
    return unified_key
