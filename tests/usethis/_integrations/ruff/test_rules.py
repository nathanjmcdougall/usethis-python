from pathlib import Path

import pytest

from usethis._integrations.pyproject.io import PyProjectTOMLNotFoundError
from usethis._integrations.ruff.rules import (
    deselect_ruff_rules,
    get_ruff_rules,
    select_ruff_rules,
)
from usethis._utils._test import change_cwd


class TestSelectRuffRules:
    def test_no_pyproject_toml(self, tmp_path: Path):
        # Act
        with change_cwd(tmp_path), pytest.raises(PyProjectTOMLNotFoundError):
            select_ruff_rules(["A", "B", "C"])

    def test_blank_slate(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text("")

        # Act
        new_rules = ["A", "B", "C"]
        with change_cwd(tmp_path):
            select_ruff_rules(new_rules)

            # Assert
            rules = get_ruff_rules()
        assert rules == new_rules

    def test_mixing(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text(
            """
[tool.ruff.lint]
select = ["A", "B"]
"""
        )

        # Act
        with change_cwd(tmp_path):
            select_ruff_rules(["C", "D"])

            # Assert
            rules = get_ruff_rules()
        assert rules == ["A", "B", "C", "D"]

    def test_respects_order(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text(
            """
[tool.ruff.lint]
select = ["D", "B", "A"]
"""
        )

        # Act
        with change_cwd(tmp_path):
            select_ruff_rules(["E", "C", "A"])

            # Assert
            assert get_ruff_rules() == ["D", "B", "A", "C", "E"]


class TestDeselectRuffRules:
    def test_no_pyproject_toml(self, tmp_path: Path):
        # Act
        with change_cwd(tmp_path), pytest.raises(PyProjectTOMLNotFoundError):
            deselect_ruff_rules(["A", "B", "C"])

    def test_blank_slate(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text("")

        # Act
        with change_cwd(tmp_path):
            deselect_ruff_rules(["A", "B", "C"])

            # Assert
            assert get_ruff_rules() == []

    def test_single_rule(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text(
            """
[tool.ruff.lint]
select = ["A"]
"""
        )

        # Act
        with change_cwd(tmp_path):
            deselect_ruff_rules(["A"])

            # Assert
            assert get_ruff_rules() == []

    def test_mix(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text(
            """
[tool.ruff.lint]
select = ["A", "B", "C"]
"""
        )

        # Act
        with change_cwd(tmp_path):
            deselect_ruff_rules(["A", "C"])

            # Assert
            assert get_ruff_rules() == ["B"]