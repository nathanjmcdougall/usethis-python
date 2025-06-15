from pathlib import Path

from typer.testing import CliRunner

from usethis._interface.badge import app
from usethis._test import change_cwd


class TestPyPI:
    def test_add(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pypi"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_remove(self, tmp_path: Path):
        # Arrange
        (tmp_path / "README.md").write_text("")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pypi", "--remove"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_show(self, tmp_path: Path):
        # Arrange
        (tmp_path / "README.md").write_text("")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pypi", "--show"])

        # Assert
        assert result.exit_code == 0, result.output


class TestRuff:
    def test_add(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["ruff"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_remove(self, tmp_path: Path):
        # Arrange
        (tmp_path / "README.md").write_text("")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["ruff", "--remove"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_wrong_encoding(self, tmp_path: Path):
        # Arrange
        (tmp_path / "README.md").write_text("utf-8", encoding="utf-16")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["ruff"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_show(self, tmp_path: Path):
        # Arrange
        (tmp_path / "README.md").write_text("")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["ruff", "--show"])

        # Assert
        assert result.exit_code == 0, result.output


class TestPreCommit:
    def test_add(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pre-commit"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_remove(self, tmp_path: Path):
        # Arrange
        (tmp_path / "README.md").write_text("")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pre-commit", "--remove"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_show(self, tmp_path: Path):
        # Arrange
        (tmp_path / "README.md").write_text("")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pre-commit", "--show"])

        # Assert
        assert result.exit_code == 0, result.output


class TestUsethis:
    def test_add(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["usethis"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_remove(self, tmp_path: Path):
        # Arrange
        (tmp_path / "README.md").write_text("")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["usethis", "--remove"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_show(self, tmp_path: Path):
        # Arrange
        (tmp_path / "README.md").write_text("")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["usethis", "--show"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            == "[![usethis](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/usethis-python/usethis-python/main/assets/badge/v1.json)](https://github.com/usethis-python/usethis-python)\n"
        )


class TestUV:
    def test_add(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["uv"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_remove(self, tmp_path: Path):
        # Arrange
        (tmp_path / "README.md").write_text("")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["uv", "--remove"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_show(self, tmp_path: Path):
        # Arrange
        (tmp_path / "README.md").write_text("")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["uv", "--show"])

        # Assert
        assert result.exit_code == 0, result.output
