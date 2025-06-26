from pathlib import Path

import pytest
from typer.testing import CliRunner

from usethis._config import usethis_config
from usethis._config_file import files_manager
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.uv.call import call_uv_subprocess
from usethis._interface.tool import ALL_TOOL_COMMANDS, app
from usethis._subprocess import SubprocessFailedError, call_subprocess
from usethis._test import change_cwd
from usethis._tool.all_ import ALL_TOOLS


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

    def test_how(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["codespell", "--how"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            == """\
☐ Run 'codespell' to run the Codespell spellchecker.
"""
        )


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
        # https://github.com/usethis-python/usethis-python/issues/426

        # Arrange
        (tmp_path / "__main__.py").touch()

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            if not usethis_config.offline:
                result = runner.invoke(app, ["coverage.py"])
            else:
                result = runner.invoke(app, ["coverage.py", "--offline"])

            # Assert
            assert result.exit_code == 0, result.output
            call_subprocess(["coverage", "run", "."])

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_after_codespell(self, tmp_path: Path):
        # To check the config is valid
        # https://github.com/usethis-python/usethis-python/issues/558

        # Arrange
        (tmp_path / "pyproject.toml").write_text("""\
[project]
name = "example"
version = "0.1.0"
description = "Add your description here"

[dependency-groups]
dev = [
    "codespell>=2.4.1",
]
                                                    
[tool.codespell]
ignore-regex = ["[A-Za-z0-9+/]{100,}"]
""")

        runner = CliRunner()
        with change_cwd(tmp_path):
            # Act
            if not usethis_config.offline:
                result = runner.invoke(app, ["coverage.py"])
            else:
                result = runner.invoke(app, ["coverage.py", "--offline"])

            # Assert
            assert result.exit_code == 0, result.output
            with files_manager():
                assert ["tool", "coverage"] in PyprojectTOMLManager()

        assert "[tool.coverage]" in (tmp_path / "pyproject.toml").read_text()

    def test_how(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["coverage.py", "--how"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            == """\
☐ Run 'coverage help' to see available Coverage.py commands.
"""
        )


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
            if not usethis_config.offline:
                call_subprocess(["usethis", "tool", "deptry"])
            else:
                call_subprocess(["usethis", "tool", "deptry", "--offline"])
            assert (uv_init_dir / ".venv").exists()

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_runs(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["deptry"])

            # Assert
            assert result.exit_code == 0, result.output
            call_subprocess(["deptry", "."])

    def test_how(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["deptry", "--how"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            == """\
☐ Run 'deptry .' to run deptry.
"""
        )


class TestImportLinter:
    def test_how(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["import-linter", "--how"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            == """\
ℹ Ensure '__init__.py' files are used in your packages.
ℹ For more info see <https://docs.python.org/3/tutorial/modules.html#packages>
☐ Run 'lint-imports' to run Import Linter.
"""  # noqa: RUF001
        )


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

    def test_how(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pyproject.toml", "--how"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            == """\
☐ Populate 'pyproject.toml' with the project configuration.
ℹ Learn more at 
https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
"""  # noqa: RUF001
        )


class TestPyprojectFmt:
    def test_how(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pyproject-fmt", "--how"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            == """\
☐ Run 'pyproject-fmt pyproject.toml' to run pyproject-fmt.
"""
        )


class TestPreCommit:
    @pytest.mark.benchmark
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

    def test_how(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pre-commit", "--how"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            == """\
☐ Run 'pre-commit run --all-files' to run the hooks manually.
"""
        )

    def test_adds_okay_without_git(self, tmp_path: Path):
        """Test that pre-commit runs without a git repo."""
        # Arrange
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'example'\n")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pre-commit"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_removes_okay_without_git(self, tmp_path: Path):
        """Test that pre-commit removes without a git repo."""
        # Arrange
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'example'\n")
        (tmp_path / ".pre-commit-config.yaml").write_text("")

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pre-commit", "--remove"])

        # Assert
        assert result.exit_code == 0, result.output
        assert not (tmp_path / ".pre-commit-config.yaml").exists()


class TestRequirementsTxt:
    def test_runs(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["requirements.txt"])

        # Assert
        assert result.exit_code == 0, result.output

    def test_how(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["requirements.txt", "--how"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            == """\
☐ Install uv to use 'uv export'.
☐ Run 'uv export --no-default-groups -o=requirements.txt' to write 
'requirements.txt'.
"""
        )


class TestRuff:
    @pytest.mark.benchmark
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_cli(self, uv_init_dir: Path):
        with change_cwd(uv_init_dir):
            if not usethis_config.offline:
                call_subprocess(["usethis", "tool", "ruff"])
            else:
                call_subprocess(["usethis", "tool", "ruff", "--offline"])

    def test_readme_example(self, uv_init_dir: Path):
        """This example is used the README.md file.

        Note carefully! If this test is updated, the README.md file must be
        updated too.
        """
        # Act
        runner = CliRunner()
        with change_cwd(uv_init_dir):
            result = runner.invoke(app, ["ruff"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            # ###################################
            # See docstring!
            # ###################################
            == """\
✔ Adding dependency 'ruff' to the 'dev' group in 'pyproject.toml'.
✔ Adding Ruff config to 'pyproject.toml'.
✔ Selecting Ruff rules 'A', 'C4', 'E4', 'E7', 'E9', 'F', 'FLY', 'FURB', 'I', 
'PLE', 'PLR', 'RUF', 'SIM', 'UP' in 'pyproject.toml'.
✔ Ignoring Ruff rules 'PLR2004', 'SIM108' in 'pyproject.toml'.
☐ Run 'uv run ruff check --fix' to run the Ruff linter with autofixes.
☐ Run 'uv run ruff format' to run the Ruff formatter.
"""
        )

    def test_how(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["ruff", "--how"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            == """\
☐ Run 'ruff check --fix' to run the Ruff linter with autofixes.
☐ Run 'ruff format' to run the Ruff formatter.
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
✔ Selecting Ruff rule 'PT' in 'pyproject.toml'.
✔ Creating '/tests'.
✔ Writing '/tests/conftest.py'.
☐ Add test files to the '/tests' directory with the format 'test_*.py'.
☐ Add test functions with the format 'test_*()'.
☐ Run 'uv run pytest' to run the tests.
"""
        )

    def test_how(self, tmp_path: Path):
        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, ["pytest", "--how"])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            == """\
☐ Add test files to the '/tests' directory with the format 'test_*.py'.
☐ Add test functions with the format 'test_*()'.
☐ Run 'pytest' to run the tests.
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

    runner = CliRunner()
    with change_cwd(tmp_path):
        # Act, Assert
        result = runner.invoke(app, ["pytest"])
        assert not result.exit_code, result.stdout
        result = runner.invoke(app, ["coverage"])
        assert not result.exit_code, result.stdout
        result = runner.invoke(app, ["ruff"])
        assert not result.exit_code, result.stdout
        result = runner.invoke(app, ["deptry"])
        assert not result.exit_code, result.stdout
        result = runner.invoke(app, ["pre-commit"])
        assert not result.exit_code, result.stdout
        result = runner.invoke(app, ["ruff", "--remove"])
        assert not result.exit_code, result.stdout
        result = runner.invoke(app, ["pyproject-fmt"])
        assert not result.exit_code, result.stdout
        result = runner.invoke(app, ["pytest", "--remove"])
        assert not result.exit_code, result.stdout


def test_tool_matches_command():
    assert {tool.name.lower().replace(" ", "-") for tool in ALL_TOOLS} == set(
        ALL_TOOL_COMMANDS
    )


def test_app_commands_match_list():
    commands = app.registered_commands
    names = [command.name for command in commands]
    names.remove("coverage")  # Deprecated
    assert set(names) == set(ALL_TOOL_COMMANDS)
