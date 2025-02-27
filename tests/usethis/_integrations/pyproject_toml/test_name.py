from pathlib import Path

import pytest

from usethis._integrations.pyproject_toml.errors import (
    PyprojectTOMLProjectDescriptionError,
    PyprojectTOMLProjectNameError,
    PyprojectTOMLProjectSectionError,
)
from usethis._integrations.pyproject_toml.io_ import pyproject_toml_io_manager
from usethis._integrations.pyproject_toml.name import get_description, get_name
from usethis._test import change_cwd


class TestGetName:
    def test_basic(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "pyproject.toml"
        path.write_text(
            """\
            [project]
            name = "usethis"
            """
        )

        # Act
        with change_cwd(tmp_path), pyproject_toml_io_manager.open():
            result = get_name()

        # Assert
        assert result == "usethis"

    def test_missing_file(self, tmp_path: Path):
        # Act, Assert
        with (
            change_cwd(tmp_path),
            pyproject_toml_io_manager.open(),
            pytest.raises(FileNotFoundError),
        ):
            get_name()

    def test_missing_section(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "pyproject.toml"
        path.write_text("")

        # Act, Assert
        with (
            change_cwd(tmp_path),
            pyproject_toml_io_manager.open(),
            pytest.raises(PyprojectTOMLProjectSectionError),
        ):
            get_name()

    def test_missing_name_value(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "pyproject.toml"
        path.write_text("[project]")

        # Act, Assert
        with (
            change_cwd(tmp_path),
            pyproject_toml_io_manager.open(),
            pytest.raises(PyprojectTOMLProjectNameError),
        ):
            get_name()

    def test_invalid_name_value(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "pyproject.toml"
        path.write_text(
            """\
            [project]
            name = 42
            """
        )

        # Act, Assert
        with (
            change_cwd(tmp_path),
            pyproject_toml_io_manager.open(),
            pytest.raises(PyprojectTOMLProjectNameError),
        ):
            get_name()


class TestGetDescription:
    def test_basic(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "pyproject.toml"
        path.write_text(
            """\
            [project]
            description = "A package for doing things."
            """
        )

        # Act
        with change_cwd(tmp_path), pyproject_toml_io_manager.open():
            result = get_description()

        # Assert
        assert result == "A package for doing things."

    def test_missing_file(self, tmp_path: Path):
        # Act, Assert
        with (
            change_cwd(tmp_path),
            pyproject_toml_io_manager.open(),
            pytest.raises(FileNotFoundError),
        ):
            get_description()

    def test_missing_section(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "pyproject.toml"
        path.write_text("")

        # Act, Assert
        with (
            change_cwd(tmp_path),
            pyproject_toml_io_manager.open(),
            pytest.raises(PyprojectTOMLProjectSectionError),
        ):
            get_description()

    def test_missing_name_value(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "pyproject.toml"
        path.write_text("[project]")

        # Act, Assert
        with (
            change_cwd(tmp_path),
            pyproject_toml_io_manager.open(),
            pytest.raises(PyprojectTOMLProjectDescriptionError),
        ):
            get_description()
