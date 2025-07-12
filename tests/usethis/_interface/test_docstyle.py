from pathlib import Path

from typer.testing import CliRunner

from usethis._app import app
from usethis._test import change_cwd


class TestDocstyle:
    def test_google_runs(self, tmp_path: Path):
        with change_cwd(tmp_path):
            runner = CliRunner()
            runner.invoke(app, ["docstyle", "google"])

    def test_invalid_pyproject_toml(self, tmp_path: Path):
        # Arrange
        invalid_pyproject_toml = tmp_path / "pyproject.toml"
        invalid_pyproject_toml.write_text("[")

        # Act
        with change_cwd(tmp_path):
            runner = CliRunner()
            with change_cwd(tmp_path):
                result = runner.invoke(app, ["docstyle", "google"])

        # Assert
        assert result.exit_code == 1, result.output

    def test_pyproject_toml_success(self, tmp_path: Path):
        # https://github.com/usethis-python/usethis-python/issues/507

        # Arrange
        valid_pyproject_toml = tmp_path / "pyproject.toml"
        valid_pyproject_toml.touch()

        # Act
        with change_cwd(tmp_path):
            runner = CliRunner()
            result = runner.invoke(app, ["docstyle", "numpy"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            "✔ Setting docstring style to 'numpy' in 'pyproject.toml'." in result.output
        )

        assert valid_pyproject_toml.exists()
        content = valid_pyproject_toml.read_text()
        assert (
            """\
[tool.ruff]
line-length = 88
format.docstring-code-format = true
lint.pydocstyle.convention = "numpy"\
"""
            in content
        )

    def test_adding_to_existing_file(self, tmp_path: Path):
        # Arrange
        existing_pyproject_toml = tmp_path / "pyproject.toml"
        existing_pyproject_toml.write_text(
            """\
[project]
name = "usethis"
version = "0.1.0"

[tool.ruff]
lint.select = [ "A" ]
"""
        )

        # Act
        with change_cwd(tmp_path):
            runner = CliRunner()
            result = runner.invoke(app, ["docstyle", "pep257"])

        # Assert
        assert result.exit_code == 0, result.output
        content = existing_pyproject_toml.read_text()
        assert "[lint.pydocstyle]" not in content  # Wrong section name

    def test_default(self, tmp_path: Path):
        # Arrange
        default_pyproject_toml = tmp_path / "pyproject.toml"
        default_pyproject_toml.touch()

        # Act
        with change_cwd(tmp_path):
            runner = CliRunner()
            result = runner.invoke(app, ["docstyle"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            "✔ Setting docstring style to 'google' in 'pyproject.toml'."
            in result.output
        )

        content = default_pyproject_toml.read_text()
        assert "google" in content
