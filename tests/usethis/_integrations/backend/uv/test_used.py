from pathlib import Path

from usethis._config_file import files_manager
from usethis._integrations.backend.uv.used import is_uv_used
from usethis._test import change_cwd


class TestIsUvUsed:
    def test_empty_dir(self, tmp_path: Path):
        # Act
        with change_cwd(tmp_path), files_manager():
            result = is_uv_used()

        # Assert
        assert not result

    def test_uv_lock(self, tmp_path: Path):
        # Arrange
        (tmp_path / "uv.lock").touch()

        # Act
        with change_cwd(tmp_path):
            result = is_uv_used()

        # Assert
        assert result

    def test_uv_toml(self, tmp_path: Path):
        # Arrange
        (tmp_path / "uv.toml").touch()

        # Act
        with change_cwd(tmp_path):
            result = is_uv_used()

        # Assert
        assert result

    def test_pyproject_toml(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text("""\
[tool.uv]
foo = "bar"
""")

        # Act
        with change_cwd(tmp_path), files_manager():
            result = is_uv_used()

        # Assert
        assert result
