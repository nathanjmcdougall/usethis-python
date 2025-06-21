from pathlib import Path

import pytest


class TestPyprojectFmtTool:
    class TestPrintHowToUse:
        def test_uv_only(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
            # Arrange
            from usethis._config_file import files_manager
            from usethis._test import change_cwd
            from usethis._tool.impl.pyproject_fmt import PyprojectFmtTool

            (tmp_path / "uv.lock").touch()

            # Act
            with change_cwd(tmp_path), files_manager():
                PyprojectFmtTool().print_how_to_use()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "☐ Run 'uv run pyproject-fmt pyproject.toml' to run pyproject-fmt.\n"
            )
