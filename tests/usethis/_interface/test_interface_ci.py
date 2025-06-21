from pathlib import Path

import pytest


class TestBitbucket:
    def test_add(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._interface.ci import app
        from usethis._test import change_cwd

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(
                app,  # The CI menu only has 1 command (bitbucket
                # pipelines) so we skip the subcommand here
            )

        # Assert
        assert result.exit_code == 0, result.output
        assert (tmp_path / "bitbucket-pipelines.yml").exists()

    def test_remove(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._interface.ci import app
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text("")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(
                app, ["--remove"]
            )  # The CI menu only has 1 command (bitbucket
            # pipelines) so we skip the subcommand here

        # Assert
        assert result.exit_code == 0, result.output
        assert not (tmp_path / "bitbucket-pipelines.yml").exists()

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_maximal_config(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._app import app as main_app
        from usethis._config import usethis_config
        from usethis._interface.ci import app
        from usethis._interface.tool import ALL_TOOL_COMMANDS
        from usethis._test import change_cwd

        runner = CliRunner()
        with change_cwd(tmp_path):
            # Pin the Python version
            (tmp_path / ".python-version").write_text(
                "3.13"  # Bump to latest version of Python
            )

            for tool_command in ALL_TOOL_COMMANDS:
                if not usethis_config.offline:
                    runner.invoke(main_app, ["tool", tool_command])
                else:
                    runner.invoke(main_app, ["tool", tool_command, "--offline"])

            # Act
            runner.invoke(app)  # The CI menu only has 1 command (bitbucket
            # pipelines) so we skip the subcommand here

        # Assert
        expected_yml = (
            Path(__file__).parent / "maximal_bitbucket_pipelines.yml"
        ).read_text()
        assert (tmp_path / "bitbucket-pipelines.yml").read_text() == expected_yml

    def test_invalid_pyproject_toml(self, tmp_path: Path):
        # Arrange
        from typer.testing import CliRunner

        from usethis._interface.ci import app
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("(")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app)

        # Assert
        assert result.exit_code == 1, result.output
