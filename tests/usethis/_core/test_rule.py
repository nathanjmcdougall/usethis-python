from pathlib import Path

import pytest

from usethis._config_file import files_manager
from usethis._core.rule import (
    deselect_rules,
    ignore_rules,
    select_rules,
    unignore_rules,
)
from usethis._deps import get_deps_from_group
from usethis._test import change_cwd
from usethis._tool.impl.deptry import DeptryTool
from usethis._tool.impl.ruff import RuffTool
from usethis._types.deps import Dependency


class TestSelectRules:
    def test_ruff_gets_installed(self, uv_init_dir: Path):
        with change_cwd(uv_init_dir), files_manager():
            # Act
            select_rules(rules=["A"])

            # Assert
            assert Dependency(name="ruff") in get_deps_from_group(group="dev")

    def test_deptry_rule_selected(
        self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
    ):
        with change_cwd(uv_init_dir), files_manager():
            # Act
            select_rules(rules=["DEP001"])

            # Assert
            assert Dependency(name="deptry") in get_deps_from_group(group="dev")

        out, err = capfd.readouterr()
        assert not err
        assert out == (
            "✔ Adding dependency 'deptry' to the 'dev' group in 'pyproject.toml'.\n"
            "☐ Install the dependency 'deptry'.\n"
            "☐ Run 'uv run deptry src' to run deptry.\n"
            "ℹ All deptry rules are always implicitly selected.\n"  # noqa: RUF001
        )

    def test_success(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        with change_cwd(uv_init_dir), files_manager():
            # Arrange
            (uv_init_dir / "ruff.toml").touch()  # avoid installation messages for ruff

            # Act
            select_rules(rules=["RUF001"])

            # Assert
            assert "RUF001" in RuffTool().get_selected_rules()

        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Selecting Ruff rule 'RUF001' in 'ruff.toml'.\n"


class TestDeselectRules:
    def test_success(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        with change_cwd(uv_init_dir), files_manager():
            # Arrange
            (uv_init_dir / "ruff.toml").write_text(
                """\
[lint]
select = ["RUF001"]
"""
            )

            # Act
            deselect_rules(rules=["RUF001"])

            # Assert
            assert "RUF001" not in RuffTool().get_selected_rules()

        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Deselecting Ruff rule 'RUF001' in 'ruff.toml'.\n"


class TestUnignoreRules:
    def test_ruff(self, uv_init_dir: Path):
        with change_cwd(uv_init_dir), files_manager():
            # Arrange
            (uv_init_dir / "ruff.toml").write_text(
                """\
[lint]
ignore = ["RUF001"]
"""
            )

            # Act
            unignore_rules(rules=["RUF001"])

            # Assert
            assert "RUF001" not in RuffTool().get_ignored_rules()

    def test_deptry(self, uv_init_dir: Path):
        with change_cwd(uv_init_dir), files_manager():
            # Arrange
            (uv_init_dir / "pyproject.toml").write_text(
                """\
[tool.deptry]
ignore = ["DEP001"]
"""
            )

            # Act
            unignore_rules(rules=["DEP001"])

            # Assert
            assert "DEP001" not in DeptryTool().get_ignored_rules()


class TestIgnoreRules:
    def test_deptry_rule(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        with change_cwd(uv_init_dir), files_manager():
            # Act
            ignore_rules(rules=["DEP001"])

        # Assert
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Ignoring deptry rule 'DEP001' in 'pyproject.toml'.\n"
        assert "[tool.deptry]" in (uv_init_dir / "pyproject.toml").read_text()
