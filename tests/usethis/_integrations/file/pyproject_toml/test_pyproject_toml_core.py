import re
from pathlib import Path

import pytest

from usethis._integrations.file.pyproject_toml.errors import (
    PyprojectTOMLNotFoundError,
    PyprojectTOMLValueAlreadySetError,
    PyprojectTOMLValueMissingError,
)
from usethis._integrations.file.pyproject_toml.io_ import (
    PyprojectTOMLManager,
)
from usethis._test import change_cwd


class TestGetPyprojectValue:
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


class TestSetPyprojectValue:
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
            PyprojectTOMLManager().set_value(
                keys=["tool", "usethis", "key"], value="value2", exists_ok=True
            )

        # Assert
        assert (
            (tmp_path / "pyproject.toml").read_text()
            == """\
[tool.usethis]
key = "value2"
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
            PyprojectTOMLManager().set_value(
                keys=["tool", "usethis", "key1"], value="value3", exists_ok=True
            )

        # Assert
        assert (
            (tmp_path / "pyproject.toml").read_text()
            == """\
[tool.usethis]
key1 = "value3"
key2 = "value2"
"""
        )


class TestRemovePyprojectValue:
    def test_already_missing(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").touch()

        # Act, Assert
        with (
            change_cwd(tmp_path),
            PyprojectTOMLManager(),
            pytest.raises(PyprojectTOMLValueMissingError),
        ):
            PyprojectTOMLManager().remove_value(keys=["tool", "usethis", "key"])

    def test_missing_pyproject(self, tmp_path: Path):
        with (
            change_cwd(tmp_path),
            PyprojectTOMLManager(),
            pytest.raises(PyprojectTOMLNotFoundError),
        ):
            PyprojectTOMLManager().remove_value(keys=["tool", "usethis", "key"])

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
            PyprojectTOMLManager().remove_value(keys=["tool", "usethis", "key"])

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
            PyprojectTOMLManager().remove_value(keys=["tool", "usethis", "key1"])

        # Assert
        assert (
            (tmp_path / "pyproject.toml").read_text()
            == """\
[tool.usethis]
key2 = "value2"
"""
        )

    def test_already_missing_okay(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").touch()

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            PyprojectTOMLManager().remove_value(
                keys=["tool", "usethis", "key"], missing_ok=True
            )

        # Assert
        assert (tmp_path / "pyproject.toml").read_text() == ""


class TestExtendPyprojectList:
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
