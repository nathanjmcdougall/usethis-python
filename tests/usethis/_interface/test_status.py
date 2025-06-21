from pathlib import Path


class TestStatus:
    def test_successful(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._app import app
        from usethis._test import change_cwd

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["status", "beta"])

        # Assert
        assert result.exit_code == 0, result.output
        assert result.output == (
            "✔ Writing 'pyproject.toml'.\n✔ Setting the development status to '4 - Beta'.\n"
        )

    def test_numerical_code(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._app import app
        from usethis._test import change_cwd

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["status", "5"])

        # Assert
        assert result.exit_code == 0, result.output
        assert result.output == (
            "✔ Writing 'pyproject.toml'.\n✔ Setting the development status to '5 - Production/Stable'.\n"
        )

    def test_no_args(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._app import app
        from usethis._test import change_cwd

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["status"])

        # Assert
        assert result.exit_code == 2, result.output
