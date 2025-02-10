from pathlib import Path

import pytest
from typer.testing import CliRunner

from usethis._config import usethis_config
from usethis._interface.tool import app
from usethis._subprocess import SubprocessFailedError, call_subprocess
from usethis._test import change_cwd


class TestDeptry:
    @pytest.mark.benchmark
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_cli(self, uv_init_dir: Path):
        with change_cwd(uv_init_dir):
            if not usethis_config.offline:
                call_subprocess(["usethis", "tool", "deptry"])
            else:
                call_subprocess(["usethis", "tool", "deptry", "--offline"])

    @pytest.mark.benchmark
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_cli_frozen(self, uv_init_dir: Path):
        with change_cwd(uv_init_dir):
            call_subprocess(["usethis", "tool", "deptry", "--frozen"])
            assert not (uv_init_dir / ".venv").exists()

    @pytest.mark.benchmark
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_cli_not_frozen(self, uv_init_dir: Path):
        with change_cwd(uv_init_dir):
            call_subprocess(["usethis", "tool", "deptry"])
            assert (uv_init_dir / ".venv").exists()


class TestPreCommit:
    @pytest.mark.benchmark
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_cli_pass(self, uv_init_repo_dir: Path):
        with change_cwd(uv_init_repo_dir):
            if not usethis_config.offline:
                call_subprocess(["usethis", "tool", "pre-commit"])
            else:
                call_subprocess(["usethis", "tool", "pre-commit", "--offline"])

            call_subprocess(["uv", "run", "pre-commit", "run", "--all-files"])

    @pytest.mark.benchmark
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_cli_fail(self, uv_init_repo_dir: Path):
        with change_cwd(uv_init_repo_dir):
            if not usethis_config.offline:
                call_subprocess(["usethis", "tool", "pre-commit"])
            else:
                call_subprocess(["usethis", "tool", "pre-commit", "--offline"])

            # Pass invalid TOML to fail the pre-commit for validate-pyproject
            (uv_init_repo_dir / "pyproject.toml").write_text("[")
            try:
                call_subprocess(["uv", "run", "pre-commit", "run", "--all-files"])
            except SubprocessFailedError:
                pass
            else:
                pytest.fail("Expected subprocess.CalledProcessError")


class TestRuff:
    @pytest.mark.benchmark
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_cli(self, uv_init_dir: Path):
        with change_cwd(uv_init_dir):
            if not usethis_config.offline:
                call_subprocess(["usethis", "tool", "ruff"])
            else:
                call_subprocess(["usethis", "tool", "ruff", "--offline"])


class TestPytest:
    def test_add(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pytest"])

        # Assert
        assert result.exit_code == 0


class TestCodespell:
    def test_add(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["codespell"])

        # Assert
        assert result.exit_code == 0


@pytest.mark.benchmark
def test_several_tools_add_and_remove(tmp_path: Path):
    runner = CliRunner()
    with change_cwd(tmp_path):
        runner.invoke(app, ["pytest"])
        runner.invoke(app, ["coverage"])
        runner.invoke(app, ["ruff"])
        runner.invoke(app, ["deptry"])
        runner.invoke(app, ["pre-commit"])
        runner.invoke(app, ["ruff", "--remove"])
        runner.invoke(app, ["pyproject-fmt"])
        runner.invoke(app, ["pytest", "--remove"])
