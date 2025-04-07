from pathlib import Path

from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.file.pyproject_toml.valid import ensure_pyproject_validity
from usethis._test import change_cwd


class TestEnsurePyprojectValidity:
    def test_does_not_exist(self, tmp_path: Path):
        # Act
        with change_cwd(tmp_path):
            ensure_pyproject_validity()

        # Assert
        assert not (tmp_path / "pyproject.toml").exists()

    def test_empty(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "fun_project"
        path.mkdir()
        (path / "pyproject.toml").write_text("")

        # Act
        with change_cwd(path), PyprojectTOMLManager():
            ensure_pyproject_validity()

        # Assert
        assert (
            (path / "pyproject.toml").read_text()
            == """\
[project]
name = "fun_project"
version = "0.1.0"
"""
        )

    def test_already_name_no_version(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text(
            """\
[project]
name = "fun_project"
"""
        )

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            ensure_pyproject_validity()

        # Assert
        assert (
            (tmp_path / "pyproject.toml").read_text()
            == """\
[project]
name = "fun_project"
version = "0.1.0"
"""
        )

    def test_already_version_no_name(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "fun_project"
        path.mkdir()
        (path / "pyproject.toml").write_text(
            """\
[project]
version = "0.1.0"
"""
        )

        # Act
        with change_cwd(path), PyprojectTOMLManager():
            ensure_pyproject_validity()

        # Assert
        assert (
            (path / "pyproject.toml").read_text()
            == """\
[project]
name = "fun_project"
version = "0.1.0"
"""
        )

    def test_already_project_section(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "fun_project"
        path.mkdir()
        (path / "pyproject.toml").write_text(
            """\
[project]
something_else = "cool"
"""
        )

        # Act
        with change_cwd(path), PyprojectTOMLManager():
            ensure_pyproject_validity()

        # Assert
        assert (
            (path / "pyproject.toml").read_text()
            == """\
[project]
name = "fun_project"
something_else = "cool"
version = "0.1.0"
"""
        )

    def test_project_is_not_table(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "fun_project"
        path.mkdir()
        (path / "pyproject.toml").write_text(
            """\
project = 1
"""
        )

        # Act
        with (
            change_cwd(path),
            PyprojectTOMLManager(),
        ):
            ensure_pyproject_validity()

        # Assert
        assert (
            (path / "pyproject.toml").read_text()
            == """\
project = 1
"""
        )

    def test_dynamic_version(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "fun_project"
        path.mkdir()
        (path / "pyproject.toml").write_text(
            """\
[project]
dynamic = [ "version" ]
"""
        )

        # Act
        with change_cwd(path), PyprojectTOMLManager():
            ensure_pyproject_validity()

        # Assert
        assert (
            (path / "pyproject.toml").read_text()
            == """\
[project]
name = "fun_project"
dynamic = [ "version" ]
"""
        )

    def test_dynamic_section_in_wrong_format(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "fun_project"
        path.mkdir()
        (path / "pyproject.toml").write_text(
            """\
[project]
dynamic = 1
"""
        )

        # Act
        with change_cwd(path), PyprojectTOMLManager():
            ensure_pyproject_validity()

        # Assert
        assert (
            (path / "pyproject.toml").read_text()
            == """\
[project]
name = "fun_project"
dynamic = 1
version = "0.1.0"
"""
        )

    def test_no_alphanum_chars_in_dir_name(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "+"
        path.mkdir()
        (path / "pyproject.toml").write_text("")

        # Act
        with change_cwd(path), PyprojectTOMLManager():
            ensure_pyproject_validity()

        # Assert
        assert (
            (path / "pyproject.toml").read_text()
            == """\
[project]
name = "hello_world"
version = "0.1.0"
"""
        )

    def test_drop_nonalphanum_chars_from_dir_name(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "h-e+l.l_o"
        path.mkdir()
        (path / "pyproject.toml").write_text(
            """\
[project]
version = "0.2.0"
"""
        )

        # Act
        with change_cwd(path), PyprojectTOMLManager():
            ensure_pyproject_validity()

        # Assert
        assert (
            (path / "pyproject.toml").read_text()
            == """\
[project]
name = "h-el.l_o"
version = "0.2.0"
"""
        )
