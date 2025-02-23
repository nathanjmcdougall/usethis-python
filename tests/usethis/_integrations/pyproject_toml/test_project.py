from pathlib import Path

import pytest

from usethis._integrations.pyproject_toml.errors import (
    PyprojectTOMLNotFoundError,
    PyprojectTOMLProjectSectionError,
)
from usethis._integrations.pyproject_toml.io_ import pyproject_toml_io_manager
from usethis._integrations.pyproject_toml.project import get_project_dict
from usethis._test import change_cwd


class TestGetProjectDict:
    def test_no_file(self, tmp_path: Path):
        with (
            change_cwd(tmp_path),
            pyproject_toml_io_manager.open(),
            pytest.raises(PyprojectTOMLNotFoundError),
        ):
            get_project_dict()

    def test_empty_file(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").touch()

        # Act, Assert
        with (
            change_cwd(tmp_path),
            pyproject_toml_io_manager.open(),
            pytest.raises(PyprojectTOMLProjectSectionError),
        ):
            get_project_dict()

    def test_missing_project_section(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]\n")

        # Act, Assert
        with (
            change_cwd(tmp_path),
            pyproject_toml_io_manager.open(),
            pytest.raises(PyprojectTOMLProjectSectionError),
        ):
            get_project_dict()

    def test_invalid_project_section(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text("project = ['bad']\n")

        # Act, Assert
        with (
            change_cwd(tmp_path),
            pyproject_toml_io_manager.open(),
            pytest.raises(PyprojectTOMLProjectSectionError),
        ):
            get_project_dict()

    def test_valid_project_section(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname = 'foo'\ndescription = 'bar'\n"
        )

        # Act
        with change_cwd(tmp_path), pyproject_toml_io_manager.open():
            project = get_project_dict()

        # Assert
        assert project == {"name": "foo", "description": "bar"}
