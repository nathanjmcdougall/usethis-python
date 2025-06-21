from pathlib import Path

import pytest


class TestAddPytestDir:
    def test_exists(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.pytest.core import add_pytest_dir
        from usethis._test import change_cwd

        # Act
        with change_cwd(tmp_path):
            add_pytest_dir()

        # Assert
        assert (tmp_path / "tests").exists()

    def test_message(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._integrations.pytest.core import add_pytest_dir
        from usethis._test import change_cwd

        # Act
        with change_cwd(tmp_path):
            add_pytest_dir()

        # Assert
        out, _ = capfd.readouterr()
        assert out == "✔ Creating '/tests'.\n✔ Writing '/tests/conftest.py'.\n"

    def test_conftest_exists(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._integrations.pytest.core import add_pytest_dir
        from usethis._test import change_cwd

        (tmp_path / "tests").mkdir()

        # Act
        with change_cwd(tmp_path):
            add_pytest_dir()

        # Assert
        assert (tmp_path / "tests" / "conftest.py").exists()
        out, _ = capfd.readouterr()
        assert out == "✔ Writing '/tests/conftest.py'.\n"


class TestRemovePytestDir:
    def test_blank_slate(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.pytest.core import remove_pytest_dir
        from usethis._test import change_cwd

        # Act
        with change_cwd(tmp_path):
            remove_pytest_dir()

        # Assert
        assert not (tmp_path / "tests").exists()

    def test_dir(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.pytest.core import remove_pytest_dir
        from usethis._test import change_cwd

        (tmp_path / "tests").mkdir()

        # Act
        with change_cwd(tmp_path):
            remove_pytest_dir()

        # Assert
        assert not (tmp_path / "tests").exists()

    def test_protect_file(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.pytest.core import remove_pytest_dir
        from usethis._test import change_cwd

        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_something.py").touch()

        # Act
        with change_cwd(tmp_path):
            remove_pytest_dir()

        # Assert
        assert (tmp_path / "tests").exists()
        assert (tmp_path / "tests" / "test_something.py").exists()

    def test_roundtrip(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.pytest.core import add_pytest_dir, remove_pytest_dir
        from usethis._test import change_cwd

        with change_cwd(tmp_path):
            add_pytest_dir()

            # Act
            remove_pytest_dir()

        # Assert
        assert not (tmp_path / "tests").exists()
