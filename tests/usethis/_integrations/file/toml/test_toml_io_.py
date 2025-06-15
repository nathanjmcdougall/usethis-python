from pathlib import Path

import pytest
import tomlkit
import tomlkit.api
import tomlkit.items

from usethis._integrations.file.toml.errors import (
    TOMLValueAlreadySetError,
    TOMLValueMissingError,
)
from usethis._integrations.file.toml.io_ import TOMLFileManager
from usethis._test import change_cwd


class TestTOMLFileManager:
    class TestDumpContent:
        def test_no_content(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path):
                manager = MyTOMLFileManager()

            # Act, Assert
            with pytest.raises(ValueError, match="Content is None, cannot dump."):
                manager._dump_content()

    class TestContains:
        def test_no_keys(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            (tmp_path / "pyproject.toml").touch()

            # Act, Assert
            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                assert [] in manager

    class TestGetItem:
        def test_no_keys(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            (tmp_path / "pyproject.toml").write_text("""\
[tool.usethis]
a = "b"
""")

            # Act, Assert
            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                assert manager[[]] == {"tool": {"usethis": {"a": "b"}}}

    class TestContent:
        def test_content_setter(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path):
                manager = MyTOMLFileManager()

            # Act
            manager._content = 42  # type: ignore

            # Assert
            assert manager._content == 42

        def test_set_high_levels_of_nesting(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                # Act
                manager.set_value(
                    keys=[],
                    value={
                        "project": {"name": "usethis", "version": "0.1.0"},
                        "tool": {
                            "ruff": {
                                "lint": {
                                    "select": ["A"],
                                    "pydocstyle": {"convention": "pep257"},
                                }
                            }
                        },
                    },
                )

            # Assert
            contents = (tmp_path / "pyproject.toml").read_text()
            assert contents == (
                """\
[project]
name = "usethis"
version = "0.1.0"

[tool.ruff.lint]
select = ["A"]

[tool.ruff.lint.pydocstyle]
convention = "pep257"
"""
            )

        def test_set_high_levels_of_nesting_in_existing(self, tmp_path: Path) -> None:
            # https://github.com/usethis-python/usethis-python/issues/507
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                pyproject_toml_path = tmp_path / "pyproject.toml"
                pyproject_toml_path.write_text(
                    """\
[project]
name = "usethis"
version = "0.1.0"

[tool.ruff]
lint.select = [ "A" ]
"""
                )

                # Act
                manager.set_value(
                    keys=["tool", "ruff", "lint", "pydocstyle", "convention"],
                    value="pep257",
                )

            # Assert
            contents = (tmp_path / "pyproject.toml").read_text()
            assert contents == (
                """\
[project]
name = "usethis"
version = "0.1.0"

[tool.ruff]
lint.select = [ "A" ]
lint.pydocstyle.convention = "pep257"
"""
            )

        def test_tomlkit_high_levels_of_nesting_in_existing(self) -> None:
            # To help debug https://github.com/usethis-python/usethis-python/issues/507
            # This proves that dottedkey works.

            # Arrange
            txt = """\
[tool.ruff]
lint.select = [ "A" ]
"""

            toml_document: tomlkit.TOMLDocument = tomlkit.api.parse(txt)

            # Act
            tool_section = toml_document["tool"]
            assert isinstance(tool_section, tomlkit.items.Table)
            ruff_section = tool_section["ruff"]
            assert isinstance(ruff_section, tomlkit.items.Table)
            lint_section = ruff_section["lint"]
            assert isinstance(lint_section, tomlkit.items.Table)
            lint_section[
                tomlkit.items.DottedKey(
                    [
                        tomlkit.items.SingleKey("pydocstyle"),
                        tomlkit.items.SingleKey("convention"),
                    ]
                )
            ] = "pep257"
            # Whereas this doesn't work:
            # lint_section["pydocstyle"] = {"convention": "pep257"}  # noqa: ERA001

            # Assert
            contents = tomlkit.api.dumps(toml_document)
            assert contents == (
                """\
[tool.ruff]
lint.select = [ "A" ]
lint.pydocstyle.convention = "pep257"
"""
            )

    class TestSetValue:
        def test_no_keys(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            (tmp_path / "pyproject.toml").touch()

            # Act
            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                manager.set_value(keys=[], value={"b": "c"})

                # Assert
                assert manager._content == {"b": "c"}

        def test_inplace_modifications(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                manager[["a"]] = "b"

                original = manager._content

                # Act
                manager.set_value(keys=["c"], value="d")

                # Assert
                assert manager._content != original

        def test_root_level_already_set_raise(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                manager[["a"]] = "b"

                # Act, Assert
                with pytest.raises(
                    TOMLValueAlreadySetError,
                    match="Configuration value at root level is already set.",
                ):
                    manager.set_value(keys=[], value={"a": "c"}, exists_ok=False)

        def test_root_level_already_set_no_raise(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                manager[["a"]] = "b"

                # Act
                manager.set_value(keys=[], value={"a": "c"}, exists_ok=True)

                # Assert
                assert manager._content == {"a": "c"}

        def test_set_list(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                # Act
                manager.set_value(keys=["a"], value=["b", "c"])

                # Assert
                assert manager._content == {"a": ["b", "c"]}

        def test_set_list_overwrite(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                manager[["a"]] = ["b", "c"]

                # Act, Assert
                with pytest.raises(
                    TOMLValueAlreadySetError,
                    match="Configuration value 'a' is already set.",
                ):
                    manager.set_value(keys=["a"], value=["d"])

    class TestDelItem:
        def test_no_keys(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                # Act
                del manager[[]]

            # Assert
            assert not manager._content

        def test_inplace_modifications(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                manager[["a"]] = "b"
                original = manager._content

                # Act
                del manager[["a"]]

                # Assert
                assert manager._content != original

        def test_removing_root_level(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                manager[["a"]] = "b"

                # Act
                del manager[[]]

                # Assert
                assert not manager._content

        def test_removing_doesnt_exist(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                manager[["a"]] = "b"

                # Act
                with pytest.raises(TOMLValueMissingError):
                    del manager[["c"]]

    class TestExtendList:
        def test_inplace_modifications(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                manager[["a"]] = ["b", "c"]

                # Act
                manager.extend_list(keys=["a"], values=["d"])

                # Assert
                assert manager._content == {"a": ["b", "c", "d"]}

        def test_no_keys_raises(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                # Act, Assert
                with pytest.raises(
                    ValueError, match="At least one ID key must be provided."
                ):
                    manager.extend_list(keys=[], values=["d"])

        def test_doesnt_exist_yet(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                # Act
                manager.extend_list(keys=["a"], values=["b"])

                # Assert
                assert manager._content == {"a": ["b"]}

    class TestRemoveFromList:
        def test_inplace_modifications(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                manager[["a"]] = ["b", "c", "d"]

                # Act
                manager.remove_from_list(keys=["a"], values=["c"])

                # Assert
                assert manager._content == {"a": ["b", "d"]}

        def test_no_keys_raises(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                # Act, Assert
                with pytest.raises(
                    ValueError, match="At least one ID key must be provided."
                ):
                    manager.remove_from_list(keys=[], values=["d"])

        def test_already_not_present(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                manager[["b"]] = ["c"]

                original = manager._content

                # Act
                manager.remove_from_list(keys=["a"], values=["d"])

                # Assert
                assert manager._content == original

        def test_key_not_present(self, tmp_path: Path) -> None:
            # Arrange
            class MyTOMLFileManager(TOMLFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("pyproject.toml")

            with change_cwd(tmp_path), MyTOMLFileManager() as manager:
                (tmp_path / "pyproject.toml").touch()

                manager[["a"]] = ["b", "c"]

                # Act
                manager.remove_from_list(keys=["d"], values=["e"])

                # Assert
                assert manager._content == {"a": ["b", "c"]}
