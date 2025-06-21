from pathlib import Path


class TestBrowse:
    def test_success(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._interface.browse import app
        from usethis._test import change_cwd

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["usethis"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_missing_package_name(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._interface.browse import app
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, [])

        # Assert
        assert result.exit_code == 2, result.output
