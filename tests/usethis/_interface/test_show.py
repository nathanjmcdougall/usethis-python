from pathlib import Path


class TestName:
    def test_output(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._interface.show import app
        from usethis._test import change_cwd

        path = tmp_path / "fun"
        path.mkdir()

        # Act
        runner = CliRunner()
        with change_cwd(path):
            result = runner.invoke(app, ["name"])

        # Assert
        assert result.exit_code == 0, result.output
        assert result.output == """fun\n"""

    def test_invalid_pyproject(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._interface.show import app
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("[")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["name"])

        # Assert
        assert result.exit_code == 1, result.output


class TestSonarqube:
    def test_runs(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._interface.show import app
        from usethis._test import change_cwd

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
            result = runner.invoke(app, ["sonarqube"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_missing_key(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._interface.show import app
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").touch()

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["sonarqube"])

        # Assert
        assert result.exit_code == 1, result.output

    def test_invalid_pyproject(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._interface.show import app
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("[")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["sonarqube"])

        # Assert
        assert result.exit_code == 1, result.output
