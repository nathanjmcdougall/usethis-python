from pathlib import Path

import pytest
from configupdater import ConfigUpdater

from usethis._integrations.file.ini.errors import (
    INIDecodeError,
    ININotFoundError,
    INIValueAlreadySetError,
    UnexpectedINIIOError,
    UnexpectedINIOpenError,
)
from usethis._integrations.file.ini.io_ import INIFileManager
from usethis._test import change_cwd


class TestINIFileManager:
    class TestEnter:
        def test_nested_context_manager(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value")

            # Act, Assert
            with (
                change_cwd(tmp_path),
                MyINIFileManager(),
                pytest.raises(UnexpectedINIOpenError),
                MyINIFileManager(),
            ):
                pass

    class TestReadFile:
        def test_invalid_file(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("invalid.ini")

            invalid_file = tmp_path / "invalid.ini"
            invalid_file.write_text("This is not a valid INI file format.")

            # Act, Assert
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
                pytest.raises(INIDecodeError),
            ):
                manager.read_file()

        def test_file_not_found(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("non_existent.ini")

            # Act, Assert
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
                pytest.raises(ININotFoundError),
            ):
                manager.read_file()

        def test_manager_not_used(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value")

            # Act, Assert
            with change_cwd(tmp_path), pytest.raises(UnexpectedINIIOError):
                MyINIFileManager().read_file()

        def test_content_unexpectedly_not_none(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value")

            # Act
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
            ):
                manager._content = 42  # type: ignore
                with pytest.raises(UnexpectedINIIOError):
                    manager.read_file()

    class TestDumpContent:
        def test_no_content_to_dump(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.touch()

            # Act, Assert
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
                pytest.raises(ValueError, match="Content is None, cannot dump."),
            ):
                manager._dump_content()

    class TestParseContent:
        def test_type(self):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            # Act
            result = MyINIFileManager()._parse_content("[section]\nkey=value")

            # Assert
            assert isinstance(result, ConfigUpdater)

        def test_content(self):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            # Act
            result = MyINIFileManager()._parse_content("[section]\nkey=value")

            # Assert
            assert result["section"]["key"].value == "value"

    class TestContains:
        def test_option_key_exists(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = ["section", "key"] in manager

            # Assert
            assert result is True

        def test_section_key_exists(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = ["section"] in manager

            # Assert
            assert result is True

        def test_option_key_doesnt_exist(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = ["section", "nope"] in manager

            # Assert
            assert result is False

        def test_section_key_doesnt_exist(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = ["nope", "key"] in manager

            # Assert
            assert result is False

        def test_colon_in_section_name(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[colon:section]\nkey=value")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = ["colon:section"] in manager

            # Assert
            assert result is True

        def test_root_level_and_file_exists(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = [] in manager

            # Assert
            assert result is True

        def test_root_level_and_file_doesnt_exist(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = [] in manager

            # Assert
            assert result is False

        def test_multiple_sections(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value\n[other]\nkey=other")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = ["section"] in manager

            # Assert
            assert result is True

        def test_multiple_options(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value\nkey2=other")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = ["section", "key"] in manager

            # Assert
            assert result is True

        def test_nested_keys_raises(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = ["section", "key", "extra"] in manager

            # Assert
            assert result is False

    class TestGetItem:
        def test_file_doesnt_exist_raises(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            # Act
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
                pytest.raises(ININotFoundError),
            ):
                manager[["nope"]]

        def test_no_keys_gives_root(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = manager[[]]

            # Assert
            assert result == {"section": {"key": "value"}}

        def test_section_key_exists(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = manager[["section"]]

            # Assert
            assert result == {"key": "value"}

        def test_section_key_doesnt_exist(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value")

            # Act
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
                pytest.raises(KeyError),
            ):
                manager[["nope"]]

        def test_option_key_exists(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = manager[["section", "key"]]

            # Assert
            assert result == "value"

        def test_too_many_keys(self, tmp_path: Path):
            # i.e. more than 2

            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value")
            # Act, Assert
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
                pytest.raises(KeyError),
            ):
                manager[["section", "key", "extra"]]

        def test_list(self, tmp_path: Path):
            "We always return strings as values for INI files!"

            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=1, 2, 3")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = manager[["section", "key"]]

            # Assert
            assert result == "1, 2, 3"

        def test_int(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=1")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = manager[["section", "key"]]

            # Assert
            assert result == "1"

        def test_multiple_sections(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value\n[other]\nkey=other")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = manager[["section", "key"]]

            # Assert
            assert result == "value"

        def test_multiple_options(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("[section]\nkey=value\nkey2=other")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                result = manager[["section", "key"]]

            # Assert
            assert result == "value"

    class TestSetValue:
        def test_add_root_no_change(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section]
key = value
""")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.set_value(
                    keys=[], value={"section": {"key": "value"}}, exists_ok=True
                )

            # Assert
            assert (tmp_path / "valid.ini").read_text() == (
                """\
[section]
key = value
"""
            )

        def test_multiple_sections(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section]
key = value
[other]
key = other
""")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.set_value(
                    keys=["section"], value={"key": "new_value"}, exists_ok=True
                )

            # Assert
            assert (tmp_path / "valid.ini").read_text() == (
                """\
[section]
key = new_value
[other]
key = other
"""
            )

        def test_list(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.touch()
            # Act
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
                pytest.raises(NotImplementedError),
            ):
                manager.set_value(
                    keys=["section"], value={"key": [1, 2, 3]}, exists_ok=True
                )

        def test_int(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.touch()
            # Act
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
                pytest.raises(NotImplementedError),
            ):
                manager.set_value(keys=["section"], value={"key": 1}, exists_ok=True)

        def test_no_spacing_roundtrip(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section]
key=value
other_key=other_value
""")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.set_value(
                    keys=["section", "key"], value="new_value", exists_ok=True
                )

            # Assert
            assert (tmp_path / "valid.ini").read_text() == (
                """\
[section]
key = new_value
other_key=other_value
"""
            )

        def test_empty(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.touch()

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.set_value(
                    keys=[], value={"section": {"key": "new_value"}}, exists_ok=True
                )

            # Assert
            assert (tmp_path / "valid.ini").read_text() == (
                """\
[section]
key = new_value
"""
            )

        def test_overwrite_section(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section]
key = value
[other]
key = other
""")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.set_value(
                    keys=["section"], value={"new_key": "new_value"}, exists_ok=True
                )

            # Assert
            assert (tmp_path / "valid.ini").read_text() == (
                """\
[section]
new_key = new_value
[other]
key = other
"""
            )

        def test_overwrite_root(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section]
key = value
[other]
key = other
""")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.set_value(
                    keys=[],
                    value={"new_section": {"new_key": "new_value"}},
                    exists_ok=True,
                )

            # Assert
            assert (tmp_path / "valid.ini").read_text() == (
                """\
[new_section]
new_key = new_value
"""
            )

        def test_exists_ok_false_root(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section]
key = value
[other]
key = other
""")

            # Act
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
                pytest.raises(INIValueAlreadySetError),
            ):
                manager.set_value(
                    keys=[],
                    value={"section": {"key": "new_value"}},
                    exists_ok=False,
                )

        def test_sections_keep_positions_setting_root(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section1]
key = value1
[section2]
key = value2
[section3]
key = value3                               
""")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.set_value(
                    keys=[],
                    value={
                        "section2": {"key": "new_value"},
                        "section1": {"key": "new_value"},
                    },
                    exists_ok=True,
                )

            # Assert
            assert (tmp_path / "valid.ini").read_text() == (
                """\
[section1]
key = new_value
[section2]
key = new_value
"""
            )

        def test_options_keep_positions_setting_root(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section]
key1 = value1
key2 = value2        
key3 = value3       
""")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.set_value(
                    keys=[],
                    value={
                        "section": {"key2": "new_value", "key1": "new_value"},
                    },
                    exists_ok=True,
                )

            # Assert
            assert (tmp_path / "valid.ini").read_text() == (
                """\
[section]
key1 = new_value
key2 = new_value
"""
            )

        def test_too_many_keys(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.touch()

            # Act, Assert
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
                pytest.raises(
                    ValueError, match="INI files do not support nested config"
                ),
            ):
                manager.set_value(
                    keys=["section", "key", "extra"],
                    value="new_value",
                    exists_ok=True,
                )

        def test_already_set_in_section_not_exists_ok(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section]
key = value
""")

            # Act, Assert
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
                pytest.raises(INIValueAlreadySetError),
            ):
                manager.set_value(
                    keys=["section"], value={"key": "new_value"}, exists_ok=False
                )

        def test_already_set_in_option_not_exists_ok(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section]
key = value
""")

            # Act, Assert
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
                pytest.raises(INIValueAlreadySetError),
            ):
                manager.set_value(
                    keys=["section", "key"], value="new_value", exists_ok=False
                )

    class TestDelItem:
        def test_delete_root(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section1]
key1 = value1
[section2]
key2 = value2
""")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.__delitem__([])  # Delete all sections

            # Assert
            assert (tmp_path / "valid.ini").read_text() == ""

        def test_delete_section(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section1]
key1 = value1
[section2]
key2 = value2
""")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.__delitem__(["section1"])  # Delete section1

            # Assert
            assert (
                (tmp_path / "valid.ini").read_text()
                == """\
[section2]
key2 = value2
"""
            )

        def test_delete_option(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section1]
key1 = value1
key2 = value2
""")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.__delitem__(["section1", "key1"])  # Delete key1 in section1

            # Assert
            assert (
                (tmp_path / "valid.ini").read_text()
                == """\
[section1]
key2 = value2
"""
            )

        def test_delete_non_existent_section(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section1]
key1 = value1
""")

            # Act, Assert
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.__delitem__(
                    ["non_existent_section"]
                )  # Attempt to delete non-existent section

            # Assert the file content remains the same
            assert (
                (tmp_path / "valid.ini").read_text()
                == """\
[section1]
key1 = value1
"""
            )

        def test_delete_non_existent_option(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section1]
key1 = value1
""")

            # Act, Assert
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.__delitem__(
                    ["section1", "non_existent_key"]
                )  # Attempt to delete non-existent option

            # Assert the file content remains the same
            assert (
                (tmp_path / "valid.ini").read_text()
                == """\
[section1]
key1 = value1
"""
            )

        def test_delete_section_when_root_is_empty(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.touch()  # Create an empty file

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.__delitem__(
                    ["non_existent_section"]
                )  # Try to delete a non-existent section

            # Assert: The file should remain empty
            assert (tmp_path / "valid.ini").read_text() == ""

        def test_delete_root_when_not_empty(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section1]
key1 = value1
[section2]
key2 = value2
""")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.__delitem__([])  # Delete the entire root content

            # Assert: The file should now be empty
            assert (tmp_path / "valid.ini").read_text() == ""

        def test_cleanup_section_with_no_options(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section1]
key1 = value1

[section2]
key2 = value2
""")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                del manager[["section2", "key2"]]

            # Assert: The file should have only section1 left
            assert (
                (tmp_path / "valid.ini").read_text()
                == """\
[section1]
key1 = value1

"""
            )

        def test_too_many_keys(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.touch()

            # Act, Assert (no error raised)
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
            ):
                del manager[["section", "key", "extra"]]

        def test_delete_section_with_multiple_options(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.write_text("""\
[section1]
key1 = value1
key2 = value2

[section2]
key3 = value3
""")

            # Act
            with change_cwd(tmp_path), MyINIFileManager() as manager:
                manager.__delitem__(["section1"])  # Delete section1

            # Assert: The file should have only section2 left
            assert (
                (tmp_path / "valid.ini").read_text()
                == """\
[section2]
key3 = value3
"""
            )

    class TestExtendList:
        def test_not_implemented(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.touch()

            # Act, Assert
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
                pytest.raises(NotImplementedError),
            ):
                manager.extend_list(keys=["section", "key"], values=["new_value"])

    class TestRemoveFromList:
        def test_not_implemented(self, tmp_path: Path):
            # Arrange
            class MyINIFileManager(INIFileManager):
                @property
                def relative_path(self) -> Path:
                    return Path("valid.ini")

            valid_file = tmp_path / "valid.ini"
            valid_file.touch()

            # Act, Assert
            with (
                change_cwd(tmp_path),
                MyINIFileManager() as manager,
                pytest.raises(NotImplementedError),
            ):
                manager.remove_from_list(keys=["section", "key"], values=["new_value"])
