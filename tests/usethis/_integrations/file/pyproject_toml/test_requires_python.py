from pathlib import Path

import pytest


class TestGetRequiresPython:
    def test_lower_bound(self, tmp_path: Path):
        # Arrange
        from packaging.specifiers import SpecifierSet

        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.file.pyproject_toml.requires_python import (
            get_requires_python,
        )
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text(
            """\
[project]
requires-python = ">=3.7"
"""
        )

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            requires_python = get_requires_python()

        # Assert
        assert requires_python == SpecifierSet(">=3.7")

    def test_no_pyproject(self, tmp_path: Path):
        from usethis._integrations.file.pyproject_toml.errors import (
            PyprojectTOMLNotFoundError,
        )
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.file.pyproject_toml.requires_python import (
            get_requires_python,
        )
        from usethis._test import change_cwd

        with (
            change_cwd(tmp_path),
            PyprojectTOMLManager(),
            pytest.raises(PyprojectTOMLNotFoundError),
        ):
            get_requires_python()
