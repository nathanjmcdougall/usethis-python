from pathlib import Path

import pytest

from usethis._config_file import files_manager
from usethis._test import change_cwd
from usethis._tool.impl.import_linter import ImportLinterTool


class TestImportLinterTool:
    class TestPrintHowToUse:
        def test_pre_commit_and_uv(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            (tmp_path / "uv.lock").touch()
            (tmp_path / ".pre-commit-config.yaml").touch()
            (tmp_path / "ruff.toml").touch()

            # Act
            with change_cwd(tmp_path), files_manager():
                ImportLinterTool().print_how_to_use()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "☐ Run 'uv run pre-commit run import-linter --all-files' to run Import Linter.\n"
            )

        def test_pre_commit_no_uv(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            (tmp_path / ".pre-commit-config.yaml").touch()
            (tmp_path / "ruff.toml").touch()

            # Act
            with change_cwd(tmp_path), files_manager():
                ImportLinterTool().print_how_to_use()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "☐ Run 'pre-commit run import-linter --all-files' to run Import Linter.\n"
            )

        def test_uv_only(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
            # Arrange
            (tmp_path / "uv.lock").touch()
            (tmp_path / "ruff.toml").touch()

            # Act
            with change_cwd(tmp_path), files_manager():
                ImportLinterTool().print_how_to_use()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == ("☐ Run 'uv run lint-imports' to run Import Linter.\n")

        def test_basic(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
            # Arrange
            (tmp_path / "ruff.toml").touch()

            # Act
            with change_cwd(tmp_path), files_manager():
                ImportLinterTool().print_how_to_use()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == ("☐ Run 'lint-imports' to run Import Linter.\n")

        def test_ruff_isnt_used(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(tmp_path), files_manager():
                ImportLinterTool().print_how_to_use()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "ℹ Ensure '__init__.py' files are used in your packages.\n"  # noqa: RUF001
                "ℹ For more info see <https://docs.python.org/3/tutorial/modules.html#packages>\n"  # noqa: RUF001
                "☐ Run 'lint-imports' to run Import Linter.\n"
            )
