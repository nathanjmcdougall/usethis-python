from pathlib import Path

import pytest
from typer.testing import CliRunner

from usethis._config import usethis_config
from usethis._integrations.uv.call import call_uv_subprocess
from usethis._interface.tool import ALL_TOOL_COMMANDS, app
from usethis._subprocess import SubprocessFailedError, call_subprocess
from usethis._test import change_cwd
from usethis._tool import ALL_TOOLS


class TestCodespell:
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_add(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            if not usethis_config.offline:
                result = runner.invoke(app, ["codespell"])
            else:
                result = runner.invoke(app, ["codespell", "--offline"])

        # Assert
        assert result.exit_code == 0, result.output


class TestCoverage:
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_cli(self, uv_init_dir: Path):
        with change_cwd(uv_init_dir):
            if not usethis_config.offline:
                call_subprocess(["usethis", "tool", "coverage"])
            else:
                call_subprocess(["usethis", "tool", "coverage", "--offline"])

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_runs(self, tmp_path: Path):
        # To check the config is valid
        # https://github.com/nathanjmcdougall/usethis-python/issues/426

        # Arrange
        (tmp_path / "__main__.py").touch()

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            if not usethis_config.offline:
                result = runner.invoke(app, ["coverage"])
            else:
                result = runner.invoke(app, ["coverage", "--offline"])

            # Assert
            assert result.exit_code == 0, result.output
            call_subprocess(["coverage", "run", "."])


class TestDeptry:
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_cli(self, uv_init_dir: Path):
        with change_cwd(uv_init_dir):
            if not usethis_config.offline:
                call_subprocess(["usethis", "tool", "deptry"])
            else:
                call_subprocess(["usethis", "tool", "deptry", "--offline"])

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_cli_frozen(self, uv_init_dir: Path):
        with change_cwd(uv_init_dir):
            call_subprocess(["usethis", "tool", "deptry", "--frozen"])
            assert not (uv_init_dir / ".venv").exists()

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_cli_not_frozen(self, uv_init_dir: Path):
        with change_cwd(uv_init_dir):
            if not usethis_config.offline:
                call_subprocess(["usethis", "tool", "deptry"])
            else:
                call_subprocess(["usethis", "tool", "deptry", "--offline"])
            assert (uv_init_dir / ".venv").exists()


class TestPyprojectTOML:
    def test_add(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pyproject.toml"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_remove(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pyproject.toml", "--remove"])

        # Assert
        assert result.exit_code == 0, result.output


class TestPreCommit:
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_cli_pass(self, uv_init_repo_dir: Path):
        with change_cwd(uv_init_repo_dir):
            if not usethis_config.offline:
                call_subprocess(["usethis", "tool", "pre-commit"])
            else:
                call_subprocess(["usethis", "tool", "pre-commit", "--offline"])

            call_uv_subprocess(
                ["run", "pre-commit", "run", "--all-files"], change_toml=False
            )

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


class TestRequirementsTxt:
    def test_runs(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["requirements.txt"])

        # Assert
        assert result.exit_code == 0, result.output


class TestRuff:
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_cli(self, uv_init_dir: Path):
        with change_cwd(uv_init_dir):
            if not usethis_config.offline:
                call_subprocess(["usethis", "tool", "ruff"])
            else:
                call_subprocess(["usethis", "tool", "ruff", "--offline"])

    def test_readme_example(self, tmp_path: Path):
        """This example is used the README.md file.

        Note carefully! If this test is updated, the README.md file must be
        updated too.
        """
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["ruff"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            == """\
✔ Writing 'pyproject.toml'.
✔ Adding dependency 'ruff' to the 'dev' group in 'pyproject.toml'.
✔ Adding Ruff config to 'pyproject.toml'.
✔ Enabling Ruff rules 'A', 'C4', 'E4', 'E7', 'E9', 'EM', 'F', 'FURB', 'I', 
'PLE', 'PLR', 'RUF', 'SIM', 'UP' in 'pyproject.toml'.
✔ Ignoring Ruff rules 'PLR2004', 'SIM108' in 'pyproject.toml'.
☐ Run 'uv run ruff check --fix' to run the Ruff linter with autofixes.
☐ Run 'uv run ruff format' to run the Ruff formatter.
"""
        )


class TestPytest:
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_add(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            if not usethis_config.offline:
                result = runner.invoke(app, ["pytest"])
            else:
                result = runner.invoke(app, ["pytest", "--offline"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_readme_example(self, tmp_path: Path):
        """This example is used the README.md file.

        Note carefully! If this test is updated, the README.md file must be
        updated too.
        """
        # Arrange
        # We've already run ruff...
        (tmp_path / "pyproject.toml").write_text("""\
[project]
name = "example"
version = "0.1.0"     

[tool.ruff]
line-length = 88                                       
""")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pytest"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            == """\
✔ Adding dependency 'pytest' to the 'test' group in 'pyproject.toml'.
✔ Adding pytest config to 'pyproject.toml'.
✔ Enabling Ruff rule 'PT' in 'pyproject.toml'.
✔ Creating '/tests'.
✔ Writing '/tests/conftest.py'.
☐ Add test files to the '/tests' directory with the format 'test_*.py'.
☐ Add test functions with the format 'test_*()'.
☐ Run 'uv run pytest' to run the tests.
"""
        )


@pytest.mark.benchmark
def test_several_tools_add_and_remove(tmp_path: Path):
    # Arrange
    # The rationale for using src layout is to avoid writing
    # hatch config unnecessarily slowing down I/O
    tmp_path = tmp_path / "benchmark"  # To get a fixed project name
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src" / "benchmark").mkdir(exist_ok=True)
    (tmp_path / "src" / "benchmark" / "__init__.py").touch(exist_ok=True)

    # Act
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


def test_tool_matches_command():
    assert {tool.name.lower().replace(" ", "-") for tool in ALL_TOOLS} == set(
        ALL_TOOL_COMMANDS
    )


def test_app_commands_match_list():
    commands = app.registered_commands
    names = [command.name for command in commands]
    assert set(names) == set(ALL_TOOL_COMMANDS)
