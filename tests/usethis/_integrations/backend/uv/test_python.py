from pathlib import Path

import pytest

from usethis._integrations.backend.uv.python import (
    _parse_python_version_from_uv_output,
    get_available_python_versions,
    get_supported_major_python_versions,
)
from usethis._integrations.file.pyproject_toml.errors import PyprojectTOMLNotFoundError
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.python.version import (
    extract_major_version,
    get_python_version,
)
from usethis._test import change_cwd


class TestGetAvailablePythonVersions:
    def test_nonempty(self):
        # Act
        results = get_available_python_versions()

        # Assert
        assert results


class TestGetSupportedMajorPythonVersions:
    def test_lower_bound(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text(
            """\
[project]
requires-python = ">=3.10,<3.12"
"""
        )

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            supported_major_python = get_supported_major_python_versions()

        # Assert
        assert supported_major_python == [10, 11]

    def test_upper_bound(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text(
            """\
[project]
requires-python = ">=3.9,<3.12"
"""
        )

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            supported_major_python = get_supported_major_python_versions()

        # Assert
        assert supported_major_python == [9, 10, 11]

    def test_no_pyproject(self, tmp_path: Path):
        with (
            change_cwd(tmp_path),
            PyprojectTOMLManager(),
            pytest.raises(PyprojectTOMLNotFoundError),
        ):
            get_supported_major_python_versions()

    def test_no_requires_python(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text(
            """\
[project]
name = "foo"
"""
        )

        # Act
        with (
            change_cwd(tmp_path),
            PyprojectTOMLManager(),
        ):
            versions = get_supported_major_python_versions()

        # Assert
        assert versions == [extract_major_version(get_python_version())]


class TestParsePythonVersionFromUVOutput:
    def test_alpha(self):
        # Arrange
        version = "cpython-3.14.0a3+freethreaded-linux-x86_64-gnu"

        # Act
        major_version = _parse_python_version_from_uv_output(version)

        # Assert
        assert major_version == "3.14.0a3"
