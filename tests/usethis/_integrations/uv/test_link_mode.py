from pathlib import Path


class TestEnsureSymlinkMode:
    def test_symlink_mode_set(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.link_mode import ensure_symlink_mode
        from usethis._test import change_cwd

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            ensure_symlink_mode()

        # Assert
        assert (
            (tmp_path / "pyproject.toml")
            .read_text()
            .__contains__("""\
[tool.uv]
link-mode = "symlink"
""")
        )

    def test_uv_lock_takes_precedence(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.link_mode import ensure_symlink_mode
        from usethis._integrations.uv.toml import UVTOMLManager
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").touch()
        (tmp_path / "uv.toml").touch()

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager(), UVTOMLManager():
            ensure_symlink_mode()

        # Assert
        assert not (tmp_path / "pyproject.toml").read_text()
        assert (
            (tmp_path / "uv.toml")
            .read_text()
            .__contains__("""\
link-mode = "symlink"
""")
        )
