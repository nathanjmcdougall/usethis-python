from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

import mergedeep
import tomlkit.api
from pydantic import TypeAdapter
from tomlkit import TOMLDocument
from tomlkit.exceptions import TOMLKitError

from usethis._integrations.file.toml.errors import (
    TOMLDecodeError,
    TOMLNotFoundError,
    TOMLValueAlreadySetError,
    TOMLValueMissingError,
    UnexpectedTOMLIOError,
    UnexpectedTOMLOpenError,
)
from usethis._io import (
    KeyValueFileManager,
    UnexpectedFileIOError,
    UnexpectedFileOpenError,
)

if TYPE_CHECKING:
    from pathlib import Path
    from typing import ClassVar

    from typing_extensions import Self


class TOMLFileManager(KeyValueFileManager):
    _content_by_path: ClassVar[
        dict[Path, TOMLDocument | None]
    ] = {}  # TODO this isn't really shared with the child PyProjectTOMLManager class... is this a design issue?

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

    def do_keys_exist(self, keys: list[str]) -> bool:
        try:
            container = self.get()
            for key in keys:
                TypeAdapter(dict).validate_python(container)
                assert isinstance(container, dict)
                container = container[key]
        except KeyError:
            return False

        return True

    def __getitem__(self, item: list[str]) -> Any:
        id_keys = item

        if not id_keys:
            msg = "At least one ID key must be provided."
            raise ValueError(msg)

        d = self.get()
        for key in id_keys:
            TypeAdapter(dict).validate_python(d)
            assert isinstance(d, dict)
            d = d[key]

        return d

    def set_value(
        self, *, keys: list[str], value: Any, exists_ok: bool = False
    ) -> None:
        if not keys:
            msg = "At least one ID key must be provided."
            raise ValueError(msg)

        toml_document = copy.copy(self.get())

        try:
            # Index our way into each ID key.
            # Eventually, we should land at a final dict, which is the one we are setting.
            d, parent = toml_document, {}
            for key in keys:
                TypeAdapter(dict).validate_python(d)
                assert isinstance(d, dict)
                d, parent = d[key], d
        except KeyError:
            # The old configuration should be kept for all ID keys except the
            # final/deepest one which shouldn't exist anyway since we checked as much,
            # above. For example, if there is [tool.ruff] then we shouldn't overwrite it
            # with [tool.deptry]; they should coexist. So under the "tool" key, we need
            # to merge the two dicts.
            contents = value
            for key in reversed(keys):
                contents = {key: contents}
            toml_document = mergedeep.merge(toml_document, contents)  # type: ignore[reportAssignmentType]
            assert isinstance(toml_document, TOMLDocument)
        else:
            if not exists_ok:
                # The configuration is already present, which is not allowed.
                msg = f"Configuration value '{'.'.join(keys)}' is already set."
                raise TOMLValueAlreadySetError(msg)
            else:
                # The configuration is already present, but we're allowed to overwrite it.
                TypeAdapter(dict).validate_python(parent)
                assert isinstance(parent, dict)
                parent[keys[-1]] = value

        self.commit(toml_document)

    def remove_value(self, *, keys: list[str], missing_ok: bool = False) -> None:
        if not keys:
            msg = "At least one ID key must be provided."
            raise ValueError(msg)

        toml_document = copy.copy(self.get())

        # Exit early if the configuration is not present.
        try:
            d = toml_document
            for key in keys:
                TypeAdapter(dict).validate_python(d)
                assert isinstance(d, dict)
                d = d[key]
        except KeyError:
            if missing_ok:
                # Nothing to do, the configuration is already not present.
                return
            msg = f"Configuration value '{'.'.join(keys)}' is missing."
            raise TOMLValueMissingError(msg) from None

        # Remove the configuration.
        d = toml_document
        for key in keys[:-1]:
            TypeAdapter(dict).validate_python(d)
            assert isinstance(d, dict)
            d = d[key]
        assert isinstance(d, dict)
        del d[keys[-1]]

        # Cleanup: any empty sections should be removed.
        for idx in range(len(keys) - 1):
            d, parent = toml_document, {}
            TypeAdapter(dict).validate_python(d)
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

    def extend_list(self, *, keys: list[str], values: list[Any]) -> None:
        if not keys:
            msg = "At least one ID key must be provided."
            raise ValueError(msg)

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
            pyproject = mergedeep.merge(toml_document, contents)
            assert isinstance(pyproject, TOMLDocument)
        else:
            TypeAdapter(dict).validate_python(p_parent)
            TypeAdapter(list).validate_python(d)
            assert isinstance(p_parent, dict)
            assert isinstance(d, list)
            p_parent[keys[-1]] = d + values

        self.commit(toml_document)

    def remove_from_list(self, *, keys: list[str], values: list[Any]) -> None:
        if not keys:
            msg = "At least one ID key must be provided."
            raise ValueError(msg)

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
