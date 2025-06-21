from pathlib import Path


class TestGetSourceDirStr:
    def test_has_src(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.project.layout import get_source_dir_str
        from usethis._test import change_cwd

        (tmp_path / "src").mkdir()

        # Act
        with change_cwd(tmp_path):
            result = get_source_dir_str()

        # Assert
        assert result == "src"

    def test_no_src(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.project.layout import get_source_dir_str
        from usethis._test import change_cwd

        (tmp_path / "foo").mkdir()

        # Act
        with change_cwd(tmp_path):
            result = get_source_dir_str()

        # Assert
        assert result == "."

    def test_src_file_not_dir(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.project.layout import get_source_dir_str
        from usethis._test import change_cwd

        (tmp_path / "src").touch()

        # Act
        with change_cwd(tmp_path):
            result = get_source_dir_str()

        # Assert
        assert result == "."
