from pathlib import Path

from typer.testing import CliRunner

from usethis._app import app
from usethis._config_file import files_manager
from usethis._deps import get_deps_from_group
from usethis._test import change_cwd
from usethis._types.deps import Dependency


class TestSpellcheck:
    def test_dependencies_added(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["spellcheck"])

        # Assert
        assert result.exit_code == 0, result.output
        with change_cwd(tmp_path), files_manager():
            assert Dependency(name="codespell") in get_deps_from_group("dev")

    def test_how_option(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["spellcheck", "--how"])

        # Assert
        assert result.exit_code == 0, result.output
        assert result.output == "☐ Run 'codespell' to run the Codespell spellchecker.\n"

    def test_add_then_remove(self, tmp_path: Path):
        # Arrange
        runner = CliRunner()

        with change_cwd(tmp_path):
            # Act: Add spellcheck
            result = runner.invoke(app, ["spellcheck"], catch_exceptions=False)
            assert result.exit_code == 0, result.output

            # Act: Remove spellcheck
            result = runner.invoke(
                app, ["spellcheck", "--remove"], catch_exceptions=False
            )

        # Assert
        assert result.exit_code == 0, result.output
        with change_cwd(tmp_path), files_manager():
            assert Dependency(name="codespell") not in get_deps_from_group("dev")
