from pathlib import Path

from typer.testing import CliRunner

from usethis._app import app
from usethis._config_file import files_manager
from usethis._deps import get_deps_from_group
from usethis._test import change_cwd
from usethis._types.deps import Dependency


class TestLint:
    def test_dependencies_added(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["lint"])

        # Assert
        assert result.exit_code == 0, result.output
        with change_cwd(tmp_path), files_manager():
            assert Dependency(name="ruff") in get_deps_from_group("dev")
            assert Dependency(name="deptry") in get_deps_from_group("dev")

        # Check Ruff formatter is not added
        txt = (tmp_path / "pyproject.toml").read_text()
        assert "ruff.format" not in txt
        assert "ruff.lint" in txt
