from pathlib import Path


class TestVersion:
    def test_runs(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._app import app
        from usethis._test import change_cwd

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["version"])

        # Assert
        assert result.exit_code == 0, result.output
