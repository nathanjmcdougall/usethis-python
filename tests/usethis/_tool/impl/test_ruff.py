from pathlib import Path

import pytest

from usethis._config_file import DotRuffTOMLManager, RuffTOMLManager, files_manager
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._test import change_cwd
from usethis._tool.impl.ruff import RuffTool


class TestRuffTool:
    class TestSelectRules:
        def test_no_pyproject_toml(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with (
                change_cwd(tmp_path),
                files_manager(),
            ):
                RuffTool().select_rules(["A", "B", "C"])

                # Assert
                assert RuffTool().get_selected_rules() == ["A", "B", "C"]

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Writing 'pyproject.toml'.\n"
                "✔ Selecting Ruff rules 'A', 'B', 'C' in 'pyproject.toml'.\n"
            )

        def test_message(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
            # Arrange
            (tmp_path / "pyproject.toml").write_text("")

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().select_rules(["A", "B", "C"])

            # Assert
            out, _ = capfd.readouterr()
            assert "✔ Selecting Ruff rules 'A', 'B', 'C' in 'pyproject.toml" in out

        def test_blank_slate(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text("")

            # Act
            new_rules = ["A", "B", "C"]
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().select_rules(new_rules)

                # Assert
                rules = RuffTool().get_selected_rules()
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
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().select_rules(["C", "D"])

                # Assert
                rules = RuffTool().get_selected_rules()
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
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().select_rules(["E", "C", "A"])

                # Assert
                assert RuffTool().get_selected_rules() == ["D", "B", "A", "C", "E"]

        def test_ruff_toml(self, tmp_path: Path):
            # Arrange
            (tmp_path / "ruff.toml").write_text(
                """
[lint]
select = ["A", "B"]
"""
            )

            # Act
            with change_cwd(tmp_path), RuffTOMLManager():
                RuffTool().select_rules(["C", "D"])

                # Assert
                rules = RuffTool().get_selected_rules()

            assert rules == ["A", "B", "C", "D"]

        def test_no_rules(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """
[tool.ruff.lint]
select = ["A"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().select_rules([])

                # Assert
                assert RuffTool().get_selected_rules() == ["A"]

    class TestDeselectRules:
        def test_no_pyproject_toml(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(tmp_path), files_manager():
                RuffTool().deselect_rules(["A"])

                # Assert
                assert RuffTool().get_selected_rules() == []

        def test_blank_slate(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text("")

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().deselect_rules(["A", "B", "C"])

                # Assert
                assert RuffTool().get_selected_rules() == []

        def test_single_rule(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """
[tool.ruff.lint]
select = ["A"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().deselect_rules(["A"])

                # Assert
                assert RuffTool().get_selected_rules() == []

        def test_mix(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """
[tool.ruff.lint]
select = ["A", "B", "C"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().deselect_rules(["A", "C"])

                # Assert
                assert RuffTool().get_selected_rules() == ["B"]

        def test_ruff_toml(self, tmp_path: Path):
            # Arrange
            (tmp_path / ".ruff.toml").write_text(
                """\
[lint]
select = ["A", "B"]
"""
            )

            # Act
            with change_cwd(tmp_path), DotRuffTOMLManager():
                RuffTool().deselect_rules(["A"])

                # Assert
                assert RuffTool().get_selected_rules() == ["B"]

    class TestIgnoreRules:
        def test_add_to_existing(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
[tool.ruff.lint]
ignore = ["A", "B"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().ignore_rules(["C", "D"])

                # Assert
                assert RuffTool().get_ignored_rules() == ["A", "B", "C", "D"]

        def test_no_rules(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
[tool.ruff.lint]
ignore = ["A"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().ignore_rules([])

                # Assert
                assert RuffTool().get_ignored_rules() == ["A"]

    class TestIsLinterUsed:
        def test_neither_subtool_has_config_assume_both_used(self, tmp_path: Path):
            # Act
            with change_cwd(tmp_path), files_manager():
                assert RuffTool().is_linter_used()

        def test_formatter_used(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
[tool.ruff.format]
select = ["A"]
"""
            )
            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                assert not RuffTool().is_linter_used()

        def test_pyproject_toml(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
[tool.ruff.lint]
select = ["A"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                assert RuffTool().is_linter_used()

        def test_ruff_toml(self, tmp_path: Path):
            # Arrange
            (tmp_path / ".ruff.toml").write_text(
                """\
[lint]
select = ["A"]
"""
            )

            # Act
            with change_cwd(tmp_path), DotRuffTOMLManager():
                assert RuffTool().is_linter_used()

    class TestIsFormatterUsed:
        def test_neither_subtool_has_config_assume_both_used(self, tmp_path: Path):
            # Act
            with change_cwd(tmp_path), files_manager():
                assert RuffTool().is_formatter_used()

        def test_linter_used(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
[tool.ruff.lint]
select = ["A"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                assert not RuffTool().is_formatter_used()

        def test_pyproject_toml(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
[tool.ruff.format]
select = ["A"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                assert RuffTool().is_formatter_used()

        def test_ruff_toml(self, tmp_path: Path):
            # Arrange
            (tmp_path / ".ruff.toml").write_text(
                """\
[format]
select = ["A"]
"""
            )

            # Act
            with change_cwd(tmp_path), DotRuffTOMLManager():
                assert RuffTool().is_formatter_used()
