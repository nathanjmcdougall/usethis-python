from pathlib import Path


class TestAuthor:
    def test_add_name(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._app import app
        from usethis._test import change_cwd

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["author", "--name", "John Doe"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_add_name_email(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._app import app
        from usethis._test import change_cwd

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(
                app, ["author", "--name", "John Doe", "--email", "jdoe@example.com"]
            )

        # Assert
        assert result.exit_code == 0, result.output

    def test_missing_name(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._app import app
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["author"])

        # Assert
        assert result.exit_code == 2, result.output

    def test_error(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._app import app
        from usethis._test import change_cwd

        # Syntax error in pyproject.toml to trigger an error
        (tmp_path / "pyproject.toml").write_text("[")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["author", "--name", ""])

        # Assert
        assert result.exit_code == 1, result.output
