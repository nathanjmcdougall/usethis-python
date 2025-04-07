from pathlib import Path

import pytest

from usethis._config_file import files_manager
from usethis._core.list import UsageRow, UsageTable, get_usage_table, show_usage_table
from usethis._test import change_cwd


class TestShowUsageTable:
    def test_empty_project(
        self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
    ) -> None:
        # Act
        with change_cwd(tmp_path), files_manager():
            show_usage_table()

        # Assert
        out, err = capfd.readouterr()
        assert not err
        assert "✘ Unused"
        assert "✔ used" not in out
        assert "─" in out  # Rich style formatting


class TestGetUsageTable:
    def test_empty_project(self, tmp_path: Path):
        # Act
        with change_cwd(tmp_path), files_manager():
            table = get_usage_table()

        # Assert
        expected = UsageTable(
            title="Usage",
            rows=[
                UsageRow(category="tool", name="Codespell", status="unused"),
                UsageRow(category="tool", name="coverage", status="unused"),
                UsageRow(category="tool", name="deptry", status="unused"),
                UsageRow(category="tool", name="Import Linter", status="unused"),
                UsageRow(category="tool", name="pre-commit", status="unused"),
                UsageRow(category="tool", name="pyproject-fmt", status="unused"),
                UsageRow(category="tool", name="pyproject.toml", status="unused"),
                UsageRow(category="tool", name="pytest", status="unused"),
                UsageRow(category="tool", name="requirements.txt", status="unused"),
                UsageRow(category="tool", name="Ruff", status="unused"),
                UsageRow(category="ci", name="Bitbucket Pipelines", status="unused"),
                UsageRow(category="config", name="docstyle", status="unused"),
                UsageRow(category="", name="README", status="unused"),
            ],
        )
        assert table == expected

    def test_ruff_used(self, tmp_path: Path):
        # Arrange
        (tmp_path / "ruff.toml").touch()

        # Act
        with change_cwd(tmp_path), files_manager():
            table = get_usage_table()

        # Assert
        expected = UsageTable(
            title="Usage",
            rows=[
                UsageRow(category="tool", name="Codespell", status="unused"),
                UsageRow(category="tool", name="coverage", status="unused"),
                UsageRow(category="tool", name="deptry", status="unused"),
                UsageRow(category="tool", name="Import Linter", status="unused"),
                UsageRow(category="tool", name="pre-commit", status="unused"),
                UsageRow(category="tool", name="pyproject-fmt", status="unused"),
                UsageRow(category="tool", name="pyproject.toml", status="unused"),
                UsageRow(category="tool", name="pytest", status="unused"),
                UsageRow(category="tool", name="requirements.txt", status="unused"),
                UsageRow(category="tool", name="Ruff", status="used"),
                UsageRow(category="ci", name="Bitbucket Pipelines", status="unused"),
                UsageRow(category="config", name="docstyle", status="unused"),
                UsageRow(category="", name="README", status="unused"),
            ],
        )
        assert table == expected

    def test_uv_init_case(self, uv_init_dir: Path):
        # Act
        with change_cwd(uv_init_dir), files_manager():
            table = get_usage_table()

        # Assert
        expected = UsageTable(
            title="Usage",
            rows=[
                UsageRow(category="tool", name="Codespell", status="unused"),
                UsageRow(category="tool", name="coverage", status="unused"),
                UsageRow(category="tool", name="deptry", status="unused"),
                UsageRow(category="tool", name="Import Linter", status="unused"),
                UsageRow(category="tool", name="pre-commit", status="unused"),
                UsageRow(category="tool", name="pyproject-fmt", status="unused"),
                UsageRow(category="tool", name="pyproject.toml", status="used"),
                UsageRow(category="tool", name="pytest", status="unused"),
                UsageRow(category="tool", name="requirements.txt", status="unused"),
                UsageRow(category="tool", name="Ruff", status="unused"),
                UsageRow(category="ci", name="Bitbucket Pipelines", status="unused"),
                UsageRow(category="config", name="docstyle", status="unused"),
                UsageRow(category="", name="README", status="used"),
            ],
        )
        assert table == expected
