from pathlib import Path


class TestRule:
    def test_add(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._app import app
        from usethis._test import change_cwd

        (tmp_path / "ruff.toml").touch()

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["rule", "RUF001"])

        # Assert
        assert result.exit_code == 0, result.output
        assert result.output == """✔ Selecting Ruff rule 'RUF001' in 'ruff.toml'.\n"""

    def test_deselect(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._app import app
        from usethis._test import change_cwd

        (tmp_path / "ruff.toml").write_text(
            """\
[lint]
select = ["RUF001"]
"""
        )

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["rule", "RUF001", "--remove"])

        # Assert
        assert result.exit_code == 0, result.output
        assert result.output == """✔ Deselecting Ruff rule 'RUF001' in 'ruff.toml'.\n"""

    def test_ignore(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._app import app
        from usethis._test import change_cwd

        (tmp_path / "ruff.toml").touch()

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["rule", "RUF001", "--ignore"])

        # Assert
        assert result.exit_code == 0, result.output
        assert result.output == """✔ Ignoring Ruff rule 'RUF001' in 'ruff.toml'.\n"""

    def test_unignore(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._app import app
        from usethis._test import change_cwd

        (tmp_path / "ruff.toml").write_text(
            """\
[lint]
ignore = ["RUF001"]
"""
        )

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["rule", "RUF001", "--remove", "--ignore"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            == """✔ No longer ignoring Ruff rule 'RUF001' in 'ruff.toml'.\n"""
        )

    def test_runs_after_ignore(self, tmp_path: Path):
        # Arrange

        from usethis._config_file import files_manager
        from usethis._core.rule import ignore_rules
        from usethis._core.tool import use_deptry
        from usethis._subprocess import call_subprocess
        from usethis._test import change_cwd

        with change_cwd(tmp_path), files_manager():
            use_deptry()

            # Act
            ignore_rules(rules=["DEP001"])

            # Assert (that deptry runs without error)
            call_subprocess(["deptry", "."])
