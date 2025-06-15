import re
from pathlib import Path

import pytest
from tomlkit import TOMLDocument

from usethis._integrations.file.pyproject_toml.errors import (
    PyprojectTOMLDecodeError,
    PyprojectTOMLNotFoundError,
    PyprojectTOMLValueAlreadySetError,
    PyprojectTOMLValueMissingError,
    UnexpectedPyprojectTOMLIOError,
    UnexpectedPyprojectTOMLOpenError,
)
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._test import change_cwd


class TestPyprojectTOMLManager:
    def test_context_manager_locking(self, tmp_path: Path):
        # Arrange
        with change_cwd(tmp_path):
            manager = PyprojectTOMLManager()

        # Act & Assert
        assert not manager.is_locked()
        with manager:
            assert manager.is_locked()
        assert not manager.is_locked()

    def test_unexpected_open_error(self, tmp_path: Path):
        # Arrange
        with change_cwd(tmp_path):
            manager1 = PyprojectTOMLManager()
            manager2 = PyprojectTOMLManager()

        # Act & Assert
        with manager1, pytest.raises(UnexpectedPyprojectTOMLOpenError), manager2:
            pass

    def test_get_without_opening(self, tmp_path: Path):
        # Arrange
        with change_cwd(tmp_path):
            manager = PyprojectTOMLManager()

        # Act & Assert
        with pytest.raises(UnexpectedPyprojectTOMLIOError):
            manager.get()

    def test_commit_without_opening(self, tmp_path: Path):
        # Arrange
        with change_cwd(tmp_path):
            manager = PyprojectTOMLManager()

        # Act & Assert
        with pytest.raises(UnexpectedPyprojectTOMLIOError):
            manager.commit(TOMLDocument())

    def test_read_file_not_found(self, tmp_path: Path):
        with change_cwd(tmp_path):
            # Arrange
            manager = PyprojectTOMLManager()

            # Act & Assert
            with pytest.raises(PyprojectTOMLNotFoundError), manager:
                manager.read_file()

    def test_read_file_invalid_toml(self, tmp_path: Path):
        # Arrange
        with change_cwd(tmp_path):
            (tmp_path / "pyproject.toml").write_text("invalid_toml")

            manager = PyprojectTOMLManager()

        # Act & Assert
        with pytest.raises(PyprojectTOMLDecodeError), manager:
            manager.read_file()

    def test_commit_and_get(self, tmp_path: Path):
        with change_cwd(tmp_path):
            # Arrange
            manager = PyprojectTOMLManager()
            toml_data = TOMLDocument()
            toml_data["tool"] = {"test": "value"}

            # Act
            with manager:
                manager.commit(toml_data)
                result = manager.get()

        # Assert
        assert result == toml_data

    def test_write_file(self, tmp_path: Path):
        # Arrange
        with change_cwd(tmp_path):
            manager = PyprojectTOMLManager()
            toml_data = TOMLDocument()
            toml_data["tool"] = {"test": "value"}

        # Act
        with manager:
            manager.commit(toml_data)
            manager.write_file()

    def test_double_read_fails(self, tmp_path: Path):
        # Arrange
        with change_cwd(tmp_path):
            (tmp_path / "pyproject.toml").write_text("tool = { test = 'value' }")
            manager = PyprojectTOMLManager()

        # Act & Assert
        with manager:
            manager.read_file()
            with pytest.raises(UnexpectedPyprojectTOMLIOError):
                manager.read_file()

    def test_exit_without_lock(self, tmp_path: Path):
        # Arrange
        with change_cwd(tmp_path):
            manager = PyprojectTOMLManager()
        manager.unlock()

        # Act & Assert
        manager.__exit__(None, None, None)  # Should not raise an error

    def test_get_entails_read(self, tmp_path: Path):
        # Arrange
        with change_cwd(tmp_path):
            (tmp_path / "pyproject.toml").write_text("tool = { test = 'value' }")
            manager = PyprojectTOMLManager()

        # Act
        with manager:
            result = manager.get()

        # Assert
        assert result.value["tool"]["test"] == "value"

    class TestSetItem:
        def test_pyproject_does_not_exist(self, tmp_path: Path):
            with (
                change_cwd(tmp_path),
                PyprojectTOMLManager(),
                pytest.raises(PyprojectTOMLNotFoundError),
            ):
                PyprojectTOMLManager()[["tool", "usethis", "key"]]

        def test_key_does_not_exist(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
    [tool.usethis]
    key = "value"
    """
            )

            # Act, Assert
            with (
                change_cwd(tmp_path),
                PyprojectTOMLManager(),
                pytest.raises(KeyError),
            ):
                PyprojectTOMLManager()[["tool", "usethis", "key2"]]

        def test_single_key(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
    [tool.usethis]
    key = "value"
    """
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                value = PyprojectTOMLManager()[["tool", "usethis", "key"]]

            # Assert
            assert value == "value"

        def test_update_exists_ok(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
    [tool.usethis]
    key = "value1"
    """
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                PyprojectTOMLManager()[["tool", "usethis", "key"]] = "value2"

            # Assert
            assert (
                (tmp_path / "pyproject.toml").read_text()
                == """\
    [tool.usethis]
    key = "value2"
    """
            )

        def test_update_mixed_nested(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
    [tool.usethis]
    key1 = "value1"
    key2 = "value2"
    """
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                PyprojectTOMLManager()[["tool", "usethis", "key1"]] = "value3"

            # Assert
            assert (
                (tmp_path / "pyproject.toml").read_text()
                == """\
    [tool.usethis]
    key1 = "value3"
    key2 = "value2"
    """
            )

    class TestSetValue:
        def test_empty(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").touch()

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                PyprojectTOMLManager().set_value(
                    keys=["tool", "usethis", "key"], value="value"
                )

            # Assert
            assert (
                (tmp_path / "pyproject.toml").read_text()
                == """\
[tool.usethis]
key = "value"
"""
            )

        def test_update_not_exists_ok(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
[tool.usethis]
key = "value1"
"""
            )

            # Act
            with (
                change_cwd(tmp_path),
                PyprojectTOMLManager(),
                pytest.raises(
                    PyprojectTOMLValueAlreadySetError,
                    match=re.escape(
                        "Configuration value 'tool.usethis.key' is already set."
                    ),
                ),
            ):
                PyprojectTOMLManager().set_value(
                    keys=["tool", "usethis", "key"], value="value2", exists_ok=False
                )

        def test_coverage_to_codespell(self, tmp_path: Path):
            # https://github.com/usethis-python/usethis-python/issues/558

            # Arrange
            (tmp_path / "pyproject.toml").write_text("""\
[tool.codespell]
ignore-regex = ["[A-Za-z0-9+/]{100,}"]
""")

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager() as file_manager:
                file_manager.set_value(
                    keys=["tool", "coverage", "run", "source"], value=["."]
                )

                # Assert
                assert ["tool", "coverage"] in PyprojectTOMLManager()

            with change_cwd(tmp_path), PyprojectTOMLManager() as file_manager:
                assert ["tool", "coverage"] in PyprojectTOMLManager()

    class TestDel:
        def test_already_missing(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").touch()

            # Act, Assert
            with (
                change_cwd(tmp_path),
                PyprojectTOMLManager(),
                pytest.raises(PyprojectTOMLValueMissingError),
            ):
                del PyprojectTOMLManager()[["tool", "usethis", "key"]]

        def test_missing_pyproject(self, tmp_path: Path):
            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                del PyprojectTOMLManager()[["tool", "usethis", "key"]]

            assert not (tmp_path / "pyproject.toml").exists()

        def test_single_key(self, tmp_path: Path):
            """This checks the empty section cleanup."""
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
    [tool.usethis]
    key = "value"
    """
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                del PyprojectTOMLManager()[["tool", "usethis", "key"]]

            # Assert
            assert (tmp_path / "pyproject.toml").read_text() == ""

        def test_multi_key(self, tmp_path: Path):
            """This checks the empty section cleanup."""
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
    [tool.usethis]
    key1 = "value1"
    key2 = "value2"
    """
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                del PyprojectTOMLManager()[["tool", "usethis", "key1"]]

            # Assert
            assert (
                (tmp_path / "pyproject.toml").read_text()
                == """\
    [tool.usethis]
    key2 = "value2"
    """
            )

    class TestExtendList:
        def test_empty(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").touch()

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                PyprojectTOMLManager().extend_list(
                    keys=["tool", "usethis", "key"], values=["value"]
                )

            # Assert
            assert (
                (tmp_path / "pyproject.toml").read_text()
                == """\
[tool.usethis]
key = ["value"]
"""
            )

        def test_add_one(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
[tool.usethis]
key = ["value1"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                PyprojectTOMLManager().extend_list(
                    keys=["tool", "usethis", "key"], values=["value2"]
                )

            # Assert
            assert (
                (tmp_path / "pyproject.toml").read_text()
                == """\
[tool.usethis]
key = ["value1", "value2"]
"""
            )
