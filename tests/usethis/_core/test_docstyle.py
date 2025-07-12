from pathlib import Path

import pytest

from usethis._config_file import files_manager
from usethis._core.docstyle import use_docstyle
from usethis._core.tool import use_ruff
from usethis._integrations.backend.uv.init import ensure_pyproject_toml
from usethis._test import change_cwd
from usethis._types.docstyle import DocStyleEnum


class TestUseDocstyle:
    def test_numpy(self, tmp_path: Path):
        # Arrange
        (tmp_path / "ruff.toml").touch()

        # Act
        with change_cwd(tmp_path), files_manager():
            use_docstyle(DocStyleEnum.numpy)

        # Assert
        contents = (tmp_path / "ruff.toml").read_text()
        assert "pydocstyle" in contents
        assert 'convention = "numpy"' in contents
        assert (
            contents
            == """\
[lint]
select = ["D2", "D3", "D4"]
[lint.pydocstyle]
convention = "numpy"
"""
        )

    def test_google(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        (tmp_path / "ruff.toml").touch()

        # Act
        with change_cwd(tmp_path), files_manager():
            use_docstyle(DocStyleEnum.google)

        # Assert
        contents = (tmp_path / "ruff.toml").read_text()
        assert "pydocstyle" in contents
        assert 'convention = "google"' in contents
        assert (
            contents
            == """\
[lint]
select = ["D2", "D3", "D4"]
[lint.pydocstyle]
convention = "google"
"""
        )
        out, err = capfd.readouterr()
        assert not err
        assert out == (
            "✔ Setting docstring style to 'google' in 'ruff.toml'.\n"
            "✔ Selecting Ruff rules 'D2', 'D3', 'D4' in 'ruff.toml'.\n"
        )

    def test_pep257(self, tmp_path: Path):
        # Arrange
        (tmp_path / "ruff.toml").touch()

        # Act
        with change_cwd(tmp_path), files_manager():
            use_docstyle(DocStyleEnum.pep257)

        # Assert
        contents = (tmp_path / "ruff.toml").read_text()
        assert "pydocstyle" in contents
        assert 'convention = "pep257"' in contents
        assert (
            contents
            == """\
[lint]
select = ["D2", "D3", "D4"]
[lint.pydocstyle]
convention = "pep257"
"""
        )

    def test_pyproject_toml_numpy(self, tmp_path: Path):
        # Also tests the case that ruff isn't used yet.

        with change_cwd(tmp_path), files_manager():
            # Arrange
            ensure_pyproject_toml()

            # Act
            use_docstyle(DocStyleEnum.numpy)

        # Assert
        contents = (tmp_path / "pyproject.toml").read_text()
        assert "ruff" in contents
        assert "pydocstyle" in contents
        assert 'convention = "numpy"' in contents

    def test_dont_add_d_if_already_selected(self, tmp_path: Path):
        # Arrange
        (tmp_path / "ruff.toml").write_text(
            """\
[lint]
select = ["D123"]
"""
        )

        # Act
        with change_cwd(tmp_path), files_manager():
            use_docstyle(DocStyleEnum.numpy)

        # Assert
        contents = (tmp_path / "ruff.toml").read_text()
        assert "pydocstyle" in contents
        assert 'convention = "numpy"' in contents
        assert contents == (
            """\
[lint]
select = ["D123"]

[lint.pydocstyle]
convention = "numpy"
"""
        )

    def test_dont_add_d_if_all_already_selected_ruff(self, tmp_path: Path):
        # Arrange
        (tmp_path / "ruff.toml").write_text(
            """\
[lint]
select = ["ALL"]
"""
        )

        # Act
        with change_cwd(tmp_path), files_manager():
            use_docstyle(DocStyleEnum.numpy)

        # Assert
        contents = (tmp_path / "ruff.toml").read_text()
        assert "pydocstyle" in contents
        assert 'convention = "numpy"' in contents
        assert contents == (
            """\
[lint]
select = ["ALL"]

[lint.pydocstyle]
convention = "numpy"
"""
        )

    def test_leave_ok_config_alone(self, tmp_path: Path):
        # Arrange
        contents = """\
[lint]
select = ["D123"]
[lint.pydocstyle]
convention = "numpy"
"""
        (tmp_path / "ruff.toml").write_text(contents)

        # Act
        with change_cwd(tmp_path), files_manager():
            use_docstyle(DocStyleEnum.numpy)

        # Assert
        assert contents == (tmp_path / "ruff.toml").read_text()

    def test_adding_ruff_afterwards_allows_default_rules(self, tmp_path: Path):
        # Arrange
        (tmp_path / "ruff.toml").touch()

        # Act
        with change_cwd(tmp_path), files_manager():
            use_docstyle(DocStyleEnum.numpy)
            use_ruff()

        # Assert
        contents = (tmp_path / "ruff.toml").read_text()
        assert (
            contents
            == """\
line-length = 88
[lint]
select = ["D2", "D3", "D4", "A", "C4", "E4", "E7", "E9", "F", "FLY", "FURB", "I", "PLE", "PLR", "RUF", "SIM", "UP"]
ignore = ["PLR2004", "SIM108"]
[lint.pydocstyle]
convention = "numpy"

[format]
docstring-code-format = true
"""
        )
