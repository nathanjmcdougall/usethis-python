from pathlib import Path

from typer.testing import CliRunner

from usethis._interface.show import app
from usethis._test import change_cwd


class TestName:
    def test_output(self, tmp_path: Path):
        # Arrange
        path = tmp_path / "fun"
        path.mkdir()

        # Act
        runner = CliRunner()
        with change_cwd(path):
            result = runner.invoke(app, ["name"])

        # Assert
        assert result.exit_code == 0, result.output
        assert result.output == """fun\n"""


class TestSonarqubeConfig:
    def test_runs(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text(
            """
[tool.usethis.sonarqube]
project-key = "fun"

[tool.coverage.xml.output]
"""
        )

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["sonarqube-config"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_missing_key(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").touch()

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["sonarqube-config"])

        # Assert
        assert result.exit_code == 1, result.output
