from pathlib import Path


class TestSpellcheck:
    def test_dependencies_added(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._app import app
        from usethis._config_file import files_manager
        from usethis._integrations.uv.deps import Dependency, get_deps_from_group
        from usethis._test import change_cwd

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["test"])

        # Assert
        assert result.exit_code == 0, result.output
        with change_cwd(tmp_path), files_manager():
            assert Dependency(name="pytest") in get_deps_from_group("test")
