from pathlib import Path

import pytest
from typer.testing import CliRunner

from usethis._app import app as main_app
from usethis._config import usethis_config
from usethis._interface.ci import app
from usethis._interface.tool import ALL_TOOL_COMMANDS
from usethis._test import change_cwd


class TestBitbucket:
    def test_add(self, tmp_path: Path):
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
    def test_maximal_config(self, uv_init_repo_dir: Path):
        # N.B. uv_init_repo_dir is used since we need git if we want to add pre-commit
        runner = CliRunner()
        with change_cwd(uv_init_repo_dir):
            # Arrange
            for tool_command in ALL_TOOL_COMMANDS:
                if not usethis_config.offline:
                    result = runner.invoke(main_app, ["tool", tool_command])
                else:
                    result = runner.invoke(
                        main_app, ["tool", tool_command, "--offline"]
                    )
                assert not result.exit_code, f"{tool_command=}: {result.stdout}"

            # Act
            result = runner.invoke(app)  # The CI menu only has 1 command (bitbucket
            # pipelines) so we skip the subcommand here
            assert not result.exit_code, result.stdout

        # Assert
        expected_yml = (
            # N.B. when updating this file, check it against the validator:
            # https://bitbucket.org/product/pipelines/validator
            Path(__file__).parent / "maximal_bitbucket_pipelines.yml"
        ).read_text()
        assert (
            uv_init_repo_dir / "bitbucket-pipelines.yml"
        ).read_text() == expected_yml

    def test_invalid_pyproject_toml(self, tmp_path: Path):
        # Arrange
        (tmp_path / "pyproject.toml").write_text("(")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app)

        # Assert
        assert result.exit_code == 1, result.output
