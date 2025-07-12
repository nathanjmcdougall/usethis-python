import subprocess
import unittest
import unittest.mock
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from usethis._config import usethis_config
from usethis._config_file import RuffTOMLManager, files_manager
from usethis._core.ci import use_ci_bitbucket
from usethis._core.tool import (
    use_codespell,
    use_coverage_py,
    use_deptry,
    use_import_linter,
    use_pre_commit,
    use_pyproject_fmt,
    use_pyproject_toml,
    use_pytest,
    use_requirements_txt,
    use_ruff,
    use_tool,
)
from usethis._deps import add_deps_to_group, get_deps_from_group, is_dep_satisfied_in
from usethis._integrations.backend.uv.call import call_uv_subprocess
from usethis._integrations.backend.uv.link_mode import ensure_symlink_mode
from usethis._integrations.backend.uv.toml import UVTOMLManager
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.pre_commit.hooks import _HOOK_ORDER, get_hook_ids
from usethis._integrations.python.version import get_python_version
from usethis._test import change_cwd
from usethis._tool.all_ import ALL_TOOLS
from usethis._tool.impl.ruff import RuffTool
from usethis._types.deps import Dependency


class TestAllHooksList:
    def test_subset_hook_names(self, tmp_path: Path):
        with change_cwd(tmp_path):
            for tool in ALL_TOOLS:
                try:
                    hook_names = [
                        hook.id
                        for repo_config in tool.get_pre_commit_repos()
                        for hook in repo_config.hooks or []
                    ]
                except NotImplementedError:
                    continue
                for hook_name in hook_names:
                    assert hook_name in _HOOK_ORDER


class TestCodespell:
    class TestAdd:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_config(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
            # Arrange
            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                add_deps_to_group([Dependency(name="codespell")], "dev")
                ensure_symlink_mode()

            capfd.readouterr()

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_codespell()

            # Assert
            assert (
                (uv_init_dir / "pyproject.toml")
                .read_text()
                .__contains__(
                    """\
[tool.codespell]
ignore-regex = ["[A-Za-z0-9+/]{100,}"]
"""
                )
            )
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Adding Codespell config to 'pyproject.toml'.\n"
                "☐ Run 'uv run codespell' to run the Codespell spellchecker.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_bitbucket_integration(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                use_ci_bitbucket()
                capfd.readouterr()

                # Act
                use_codespell()

            # Assert
            contents = (uv_init_dir / "bitbucket-pipelines.yml").read_text()
            assert "codespell" in contents
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Adding dependency 'codespell' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'codespell'.\n"
                "✔ Adding 'Run Codespell' to default pipeline in 'bitbucket-pipelines.yml'.\n"
                "✔ Adding Codespell config to 'pyproject.toml'.\n"
                "☐ Run 'uv run codespell' to run the Codespell spellchecker.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_pre_commit_integration(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                use_pre_commit()
                capfd.readouterr()

                # Act
                use_codespell()

                # Assert
                # Check dependencies - shouldn't have installed codespell
                dev_deps = get_deps_from_group("dev")
                assert all(dep.name != "codespell" for dep in dev_deps)

                # Check hook names
                hook_names = get_hook_ids()
                assert "codespell" in hook_names
            # Check output
            out, err = capfd.readouterr()
            assert not err
            assert out.replace("\n", "") == (
                "✔ Adding hook 'codespell' to '.pre-commit-config.yaml'."
                "✔ Adding Codespell config to 'pyproject.toml'."
                "☐ Run 'uv run pre-commit run codespell --all-files' to run the Codespell spellchecker."
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_runs(self, uv_env_dir: Path):
            # An env is needed in which to run codespell

            with change_cwd(uv_env_dir), PyprojectTOMLManager():
                # Arrange
                use_codespell()

                # Act, Assert (no errors)
                call_uv_subprocess(["run", "codespell"], change_toml=False)

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_codespell_rc_file(self, uv_init_dir: Path):
            # This file is only preferred to pyproject.toml if there's already
            # some codespell config in the file

            # Arrange
            (uv_init_dir / ".codespellrc").write_text(
                """\
[codespell]
fake = bar
"""
            )

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_codespell()

            # Assert
            assert (uv_init_dir / ".codespellrc").read_text() == (
                """\
[codespell]
fake = bar
ignore-regex = [A-Za-z0-9+/]{100,}
ignore-words-list = ...
"""
            )

        def test_adding_twice(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # https://github.com/usethis-python/usethis-python/issues/509

            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                use_codespell()
                capfd.readouterr()

                # Act
                use_codespell()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "☐ Run 'uv run codespell' to run the Codespell spellchecker.\n"
            )

        def test_setup_cfg_nonempty(self, uv_init_dir: Path):
            # https://github.com/usethis-python/usethis-python/issues/542
            # Basically we want to make sure the "first_content" resolution strategy
            # works correctly.

            # Arrange
            content = """\
[codespell]
foo = bar
"""
            (uv_init_dir / "setup.cfg").write_text(content)

            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                use_codespell()

            # Assert
            assert (uv_init_dir / "setup.cfg").read_text() != content
            assert (
                "[tool.codespell]" not in (uv_init_dir / "pyproject.toml").read_text()
            )

        def test_setup_cfg_empty(self, uv_init_dir: Path):
            # https://github.com/usethis-python/usethis-python/issues/542
            # Basically we want to make sure the "first_content" resolution strategy
            # works correctly.

            # Arrange
            (uv_init_dir / "setup.cfg").touch()

            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                use_codespell()

            # Assert
            assert (uv_init_dir / "setup.cfg").read_text() == ""
            assert "[tool.codespell]" in (uv_init_dir / "pyproject.toml").read_text()

    class TestRemove:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_config_file(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            (uv_init_dir / "pyproject.toml").write_text(
                """\
[tool.codespell]
foo = "bar"
"""
            )

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_codespell(remove=True)

            # Assert
            assert (uv_init_dir / "pyproject.toml").read_text() == ""
            out, err = capfd.readouterr()
            assert not err
            assert out == ("✔ Removing Codespell config from 'pyproject.toml'.\n")

        def test_doesnt_add_pyproject(self, tmp_path: Path):
            # No pyproject.toml file to begin with...

            # Act
            with change_cwd(tmp_path), files_manager():
                use_codespell(remove=True)

            # Assert
            assert not (tmp_path / "pyproject.toml").exists()


class TestCoverage:
    class TestAdd:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_from_nothing(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_dir), files_manager():
                # Act
                use_coverage_py()

                # Assert
                assert Dependency(
                    name="coverage", extras=frozenset({"toml"})
                ) in get_deps_from_group("test")

                assert ["tool", "uv", "default-groups"] in PyprojectTOMLManager()

            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Adding dependency 'coverage' to the 'test' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'coverage'.\n"
                "✔ Adding Coverage.py config to 'pyproject.toml'.\n"
                "☐ Run 'uv run coverage help' to see available Coverage.py commands.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_no_pyproject_toml(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            # Set python version
            (tmp_path / ".python-version").write_text(get_python_version())

            with change_cwd(tmp_path), files_manager():
                # Act
                use_coverage_py()

                # Assert
                assert Dependency(
                    name="coverage", extras=frozenset({"toml"})
                ) in get_deps_from_group("test")
                out, err = capfd.readouterr()
                assert not err
                assert out == (
                    "✔ Writing 'pyproject.toml'.\n"
                    "✔ Adding dependency 'coverage' to the 'test' group in 'pyproject.toml'.\n"
                    "✔ Adding Coverage.py config to 'pyproject.toml'.\n"
                    "☐ Run 'uv run coverage help' to see available Coverage.py commands.\n"
                )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_pytest_integration(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                with usethis_config.set(quiet=True):
                    use_pytest()

                # Act
                use_coverage_py()

                # Assert
                assert Dependency(
                    name="coverage", extras=frozenset({"toml"})
                ) in get_deps_from_group("test")
                out, err = capfd.readouterr()
                assert not err
                assert out == (
                    "✔ Adding dependencies 'coverage', 'pytest-cov' to the 'test' group in \n'pyproject.toml'.\n"
                    "☐ Install the dependencies 'coverage', 'pytest-cov'.\n"
                    "✔ Adding Coverage.py config to 'pyproject.toml'.\n"
                    "☐ Run 'uv run pytest --cov' to run your tests with Coverage.py.\n"
                )

        def test_coverage_rc_file(self, uv_init_dir: Path):
            # Arrange
            (uv_init_dir / ".coveragerc").write_text("")

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_coverage_py()

            # Assert
            assert (uv_init_dir / ".coveragerc").read_text() == (
                """\
[run]
source =
    src

[report]
exclude_also =
    if TYPE_CHECKING:
    raise AssertionError
    raise NotImplementedError
    assert_never(.*)
    class .*\\bProtocol\\):
    @(abc\\.)?abstractmethod
omit =
    */pytest-of-*/*
"""
            )

        def test_tox_ini_file(self, uv_init_dir: Path):
            # Arrange
            (uv_init_dir / "tox.ini").touch()

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_coverage_py()

            # Assert
            assert (uv_init_dir / "tox.ini").read_text() == (
                """\
[coverage:run]
source =
    src

[coverage:report]
exclude_also =
    if TYPE_CHECKING:
    raise AssertionError
    raise NotImplementedError
    assert_never(.*)
    class .*\\bProtocol\\):
    @(abc\\.)?abstractmethod
omit =
    */pytest-of-*/*
"""
            )

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

        # Act
        with change_cwd(tmp_path), files_manager():
            use_coverage_py()

            # Assert
            assert ["tool", "coverage"] in PyprojectTOMLManager()
        content = (tmp_path / "pyproject.toml").read_text()
        assert "[tool.coverage]" in content

    class TestRemove:
        def test_unused(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                # Act
                use_coverage_py(remove=True)

                # Assert
                assert not get_deps_from_group("test")
                out, err = capfd.readouterr()
                assert not out  # Should not be removing anything
                assert not err

        def test_roundtrip(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                with usethis_config.set(quiet=True):
                    use_coverage_py()

                # Act
                use_coverage_py(remove=True)

                # Assert
                assert not get_deps_from_group("test")
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Removing Coverage.py config from 'pyproject.toml'.\n"
                "✔ Removing dependency 'coverage' from the 'test' group in 'pyproject.toml'.\n"
            )

        def test_pytest_integration(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                with usethis_config.set(quiet=True):
                    use_pytest()
                    use_coverage_py()

                # Act
                use_coverage_py(remove=True)

                # Assert
                assert get_deps_from_group("test") == [Dependency(name="pytest")]
                out, err = capfd.readouterr()
                assert not err
                assert out == (
                    "✔ Removing Coverage.py config from 'pyproject.toml'.\n"
                    "✔ Removing dependencies 'coverage', 'pytest-cov' from the 'test' group in \n'pyproject.toml'.\n"
                )

        def test_doesnt_add_pyproject(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # No pyproject.toml file to begin with...

            # Act
            with change_cwd(tmp_path), files_manager():
                use_coverage_py(remove=True)

            # Assert
            assert not (tmp_path / "pyproject.toml").exists()
            out, err = capfd.readouterr()
            assert not out


class TestDeptry:
    class TestAdd:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_dependency_added(self, uv_init_dir: Path):
            # Act
            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                use_deptry()

                # Assert
                (dev_dep,) = get_deps_from_group("dev")
            assert dev_dep == Dependency(name="deptry")

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_stdout(
            self,
            uv_init_dir: Path,
            capfd: pytest.CaptureFixture[str],
        ):
            # Act
            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                use_deptry()

            # Assert
            out, _ = capfd.readouterr()
            assert out == (
                "✔ Adding dependency 'deptry' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'deptry'.\n"
                "☐ Run 'uv run deptry src' to run deptry.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_stdout_unfrozen(
            self,
            uv_init_dir: Path,
            capfd: pytest.CaptureFixture[str],
        ):
            # The idea here is we make sure that the 'uv run' prefix is added

            # Act
            with (
                change_cwd(uv_init_dir),
                PyprojectTOMLManager(),
                usethis_config.set(frozen=False),
            ):
                use_deptry()

            # Assert
            out, _ = capfd.readouterr()
            assert out == (
                "✔ Adding dependency 'deptry' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Run 'uv run deptry src' to run deptry.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_run_deptry_fail(self, uv_init_dir: Path, uv_path: Path):
            # Arrange
            f = uv_init_dir / "bad.py"
            f.write_text("import broken_dependency")

            # Act
            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                use_deptry()

            # Assert
            with pytest.raises(subprocess.CalledProcessError):
                subprocess.run(
                    [uv_path.as_posix(), "run", "deptry", "."],
                    cwd=uv_init_dir,
                    check=True,
                )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_run_deptry_pass(self, uv_init_dir: Path):
            # Arrange
            f = uv_init_dir / "good.py"
            f.write_text("import sys")

            with (
                change_cwd(uv_init_dir),
                PyprojectTOMLManager(),
                usethis_config.set(frozen=False),
            ):
                # Act
                use_deptry()

                # Assert
                call_uv_subprocess(["run", "deptry", "."], change_toml=False)

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_pre_commit_after(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_deptry()
                use_pre_commit()

                # Assert
                hook_names = get_hook_ids()

            # 1. File exists
            assert (uv_init_dir / ".pre-commit-config.yaml").exists()

            # 2. Hook is in the file
            assert "deptry" in hook_names

            # 3. Test file contents
            assert (uv_init_dir / ".pre-commit-config.yaml").read_text() == (
                """\
repos:
  - repo: local
    hooks:
      - id: deptry
        name: deptry
        always_run: true
        entry: uv run --frozen --offline deptry src
        language: system
        pass_filenames: false
"""
            )

            # 4. Check messages
            out, _ = capfd.readouterr()
            assert out == (
                "✔ Adding dependency 'deptry' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'deptry'.\n"
                "☐ Run 'uv run deptry src' to run deptry.\n"
                "✔ Adding dependency 'pre-commit' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'pre-commit'.\n"
                "✔ Writing '.pre-commit-config.yaml'.\n"
                "✔ Adding hook 'deptry' to '.pre-commit-config.yaml'.\n"
                "☐ Run 'uv run pre-commit install' to register pre-commit.\n"
                "☐ Run 'uv run pre-commit run --all-files' to run the hooks manually.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_bitbucket_integration_no_pre_commit(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_ci_bitbucket()

                # Act
                use_deptry()

            # Assert
            contents = (uv_init_repo_dir / "bitbucket-pipelines.yml").read_text()
            assert "deptry" in contents

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_bitbucket_integration_with_pre_commit(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_ci_bitbucket()
                use_pre_commit()

                # Act
                use_deptry()

            # Assert
            contents = (uv_init_repo_dir / "bitbucket-pipelines.yml").read_text()
            assert "deptry" not in contents

    class TestRemove:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_dep(self, uv_init_dir: Path):
            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                # Arrange
                add_deps_to_group([Dependency(name="deptry")], "dev")

                # Act
                use_deptry(remove=True)

                # Assert
                assert not get_deps_from_group("dev")

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_bitbucket_integration(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_ci_bitbucket()
                use_deptry()

                # Act
                use_deptry(remove=True)

            # Assert
            contents = (uv_init_repo_dir / "bitbucket-pipelines.yml").read_text()
            assert "deptry" not in contents

        def test_use_deptry_removes_config(self, tmp_path: Path):
            """Test that use_deptry removes the tool's config when removing."""
            # Arrange
            pyproject = tmp_path / "pyproject.toml"
            pyproject.write_text("""[tool.deptry]
ignore_missing = ["pytest"]
""")

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                use_deptry(remove=True)

            # Assert
            assert "[tool.deptry]" not in pyproject.read_text()

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_roundtrip(self, uv_init_dir: Path):
            # Arrange
            contents = (uv_init_dir / "pyproject.toml").read_text()

            # Act
            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                use_deptry()
                use_deptry(remove=True)

            # Assert
            assert (
                (uv_init_dir / "pyproject.toml").read_text()
                == contents
                + """\

[tool.uv]
link-mode = "symlink"

[dependency-groups]
dev = []
"""
            )

        def test_doesnt_add_pyproject(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # No pyproject.toml file to begin with...

            # Act
            with change_cwd(tmp_path), files_manager():
                use_deptry(remove=True)

            # Assert
            assert not (tmp_path / "pyproject.toml").exists()
            out, err = capfd.readouterr()
            assert not out
            assert not err

    class TestPreCommitIntegration:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_pre_commit_first(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            """Basically this checks that the placeholders gets removed."""
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_pre_commit()
                capfd.readouterr()

                # Act
                use_deptry()

                # Assert
                hook_names = get_hook_ids()

            # 1. File exists
            assert (uv_init_repo_dir / ".pre-commit-config.yaml").exists()

            # 2. Hook is in the file
            assert "deptry" in hook_names

            # 3. Test file contents
            assert (uv_init_repo_dir / ".pre-commit-config.yaml").read_text() == (
                """\
repos:
  - repo: local
    hooks:
      - id: deptry
        name: deptry
        always_run: true
        entry: uv run --frozen --offline deptry src
        language: system
        pass_filenames: false
"""
            )

            # 4. Check messages
            out, _ = capfd.readouterr()
            assert out == (
                "✔ Adding dependency 'deptry' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'deptry'.\n"
                "✔ Adding hook 'deptry' to '.pre-commit-config.yaml'.\n"
                "☐ Run 'uv run deptry src' to run deptry.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_placeholder_removed(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            (uv_init_repo_dir / ".pre-commit-config.yaml").write_text(
                """\
repos:
  - repo: local
    hooks:
      - id: placeholder
"""
            )

            # Act
            with change_cwd(uv_init_repo_dir), PyprojectTOMLManager():
                use_deptry()

            # Assert
            contents = (uv_init_repo_dir / ".pre-commit-config.yaml").read_text()
            assert "deptry" in contents
            assert "placeholder" not in contents
            out, err = capfd.readouterr()
            assert not err
            # Expecting not to get a specific message about removing the placeholder.
            assert out == (
                "✔ Adding dependency 'deptry' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'deptry'.\n"
                "✔ Adding hook 'deptry' to '.pre-commit-config.yaml'.\n"
                "☐ Run 'uv run deptry src' to run deptry.\n"
            )

        def test_remove(self, uv_init_repo_dir: Path):
            with (
                change_cwd(uv_init_repo_dir),
                files_manager(),
                usethis_config.set(quiet=True),
            ):
                # Arrange
                use_deptry()
                use_pre_commit()
                content = (uv_init_repo_dir / ".pre-commit-config.yaml").read_text()
                assert "deptry" in content

                # Act
                use_deptry(remove=True)

            # Assert
            content = (uv_init_repo_dir / ".pre-commit-config.yaml").read_text()
            assert "deptry" not in content


class TestImportLinter:
    class TestAdd:
        def test_dependency(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_import_linter()

                # Assert
                assert Dependency(name="import-linter") in get_deps_from_group("dev")

            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Adding dependency 'import-linter' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'import-linter'.\n"
                "✔ Adding Import Linter config to 'pyproject.toml'.\n"
                "ℹ Ensure '__init__.py' files are used in your packages.\n"  # noqa: RUF001
                "ℹ For more info see <https://docs.python.org/3/tutorial/modules.html#packages>\n"  # noqa: RUF001
                "☐ Run 'uv run lint-imports' to run Import Linter.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_ini_contracts(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
            # Arrange
            (tmp_path / ".importlinter").touch()
            (tmp_path / "qwerttyuiop").mkdir()
            (tmp_path / "qwerttyuiop" / "a.py").touch()
            (tmp_path / "qwerttyuiop" / "b.py").touch()
            (tmp_path / "qwerttyuiop" / "__init__.py").touch()
            (tmp_path / "qwerttyuiop" / "c").mkdir()
            (tmp_path / "qwerttyuiop" / "c" / "__init__.py").touch()

            monkeypatch.syspath_prepend(str(tmp_path))

            # Act
            with change_cwd(tmp_path), files_manager():
                use_import_linter()

            # Assert
            contents = (tmp_path / ".importlinter").read_text()
            assert contents == (
                """\
[importlinter]
root_packages =
    qwerttyuiop

[importlinter:contract:0]
name = qwerttyuiop
type = layers
layers =
    a | b | c
containers =
    qwerttyuiop
exhaustive = True
"""
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_toml_contracts(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
[project]
name = "usethis"
version = "0.1.0"
"""
            )

            (tmp_path / "a").mkdir()
            (tmp_path / "a" / "__init__.py").touch()
            (tmp_path / "b").mkdir()
            (tmp_path / "b" / "__init__.py").touch()

            monkeypatch.syspath_prepend(str(tmp_path))

            # Act
            with change_cwd(tmp_path), files_manager():
                use_import_linter()

            # Assert
            contents = (tmp_path / "pyproject.toml").read_text()
            assert contents.__contains__("""\
[tool.importlinter]
root_packages = ["a", "b"]

[[tool.importlinter.contracts]]
name = "a"
type = "layers"
layers = []
containers = ["a"]
exhaustive = true

[[tool.importlinter.contracts]]
name = "b"
type = "layers"
layers = []
containers = ["b"]
exhaustive = true
""")

        @pytest.mark.xfail(
            reason="https://github.com/usethis-python/usethis-python/issues/502"
        )
        def test_pre_commit_used_not_uv(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            (tmp_path / ".pre-commit-config.yaml").write_text(
                """\
repos:
  - repo: local
    hooks:
      - id: placeholder
"""
            )

            # Act
            with change_cwd(tmp_path), files_manager():
                use_import_linter()

            # Assert
            contents = (tmp_path / ".pre-commit-config.yaml").read_text()
            assert "import-linter" not in contents
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Adding dependency 'import-linter' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'import-linter'.\n"
                "✔ Adding Import Linter config to 'pyproject.toml'.\n"
                "☐ Run 'uv run lint-imports' to run Import Linter.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_small_contracts_dropped(
            self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
        ):
            # Arrange
            (tmp_path / ".importlinter").touch()
            (tmp_path / "qwerttyuiop").mkdir()
            (tmp_path / "qwerttyuiop" / "a.py").touch()
            (tmp_path / "qwerttyuiop" / "b.py").touch()
            (tmp_path / "qwerttyuiop" / "__init__.py").touch()
            (tmp_path / "qwerttyuiop" / "c").mkdir()
            (tmp_path / "qwerttyuiop" / "c" / "__init__.py").touch()
            (tmp_path / "qwerttyuiop" / "c" / "d").mkdir()
            (tmp_path / "qwerttyuiop" / "c" / "d" / "__init__.py").touch()

            monkeypatch.syspath_prepend(str(tmp_path))

            # Act
            with change_cwd(tmp_path), files_manager():
                use_import_linter()

            # Assert
            contents = (tmp_path / ".importlinter").read_text()
            assert contents == (
                """\
[importlinter]
root_packages =
    qwerttyuiop

[importlinter:contract:0]
name = qwerttyuiop
type = layers
layers =
    a | b | c
containers =
    qwerttyuiop
exhaustive = True
"""
            )

        def test_cyclic_excluded(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
            # Arrange
            (tmp_path / ".importlinter").touch()
            (tmp_path / "a").mkdir()
            (tmp_path / "a" / "__init__.py").touch()
            (tmp_path / "a" / "b.py").write_text("import a.c")
            (tmp_path / "a" / "c.py").write_text("import a.b")

            monkeypatch.syspath_prepend(str(tmp_path))

            # Act
            with change_cwd(tmp_path), files_manager():
                use_import_linter()

            # Assert
            contents = (tmp_path / ".importlinter").read_text()
            assert contents == (
                """\
[importlinter]
root_packages =
    a

[importlinter:contract:0]
name = a
type = layers
layers = 
containers =
    a
exhaustive = True
exhaustive_ignores =
    b
    c
"""
            )

        def test_existing_ini_match(self, tmp_path: Path):
            # Arrange
            (tmp_path / ".importlinter").write_text(
                """\
[importlinter:contract:0]
name = a
"""
            )
            (tmp_path / "a").mkdir()
            (tmp_path / "a" / "__init__.py").touch()

            # Act
            with change_cwd(tmp_path), files_manager():
                use_import_linter()

            # Assert
            contents = (tmp_path / ".importlinter").read_text()
            assert contents == (
                """\
[importlinter:contract:0]
name = a

[importlinter]
root_packages =
    a
"""
            )

        def test_existing_ini_differs(self, tmp_path: Path):
            # Arrange
            (tmp_path / ".importlinter").write_text(
                """\
[importlinter:contract:existing]
name = a
"""
            )
            (tmp_path / "a").mkdir()
            (tmp_path / "a" / "__init__.py").touch()

            # Act
            with change_cwd(tmp_path), files_manager():
                use_import_linter()

            # Assert
            contents = (tmp_path / ".importlinter").read_text()
            assert contents == (
                """\
[importlinter:contract:existing]
name = a

[importlinter]
root_packages =
    a
"""
            )

        def test_numbers_in_layer_names(self, tmp_path: Path):
            # Arrange
            (tmp_path / ".importlinter").touch()
            (tmp_path / "hillslope").mkdir()
            (tmp_path / "hillslope" / "__init__.py").touch()
            (tmp_path / "hillslope" / "s1_sample.py").touch()
            (tmp_path / "hillslope" / "s2_inspect.py").touch()

            # Act
            with change_cwd(tmp_path), files_manager():
                use_import_linter()

            # Assert
            contents = (tmp_path / ".importlinter").read_text()
            assert contents == (
                """\
[importlinter]
root_packages =
    hillslope

[importlinter:contract:0]
name = hillslope
type = layers
layers =
    s1_sample | s2_inspect
containers =
    hillslope
exhaustive = True
"""
            )

        def test_nesting(self, tmp_path: Path):
            # Arrange
            (tmp_path / ".importlinter").touch()
            (tmp_path / "hillslope").mkdir()
            (tmp_path / "hillslope" / "__init__.py").touch()
            (tmp_path / "hillslope" / "s1_sample").mkdir()
            (tmp_path / "hillslope" / "s1_sample" / "__init__.py").touch()
            (tmp_path / "hillslope" / "s1_sample" / "s2_inspect.py").touch()
            (tmp_path / "hillslope" / "s1_sample" / "s3_inspect.py").touch()
            (tmp_path / "hillslope" / "s1_sample" / "s4_inspect.py").touch()

            # Act
            with change_cwd(tmp_path), files_manager():
                use_import_linter()

            # Assert
            contents = (tmp_path / ".importlinter").read_text()
            assert contents == (
                """\
[importlinter]
root_packages =
    hillslope

[importlinter:contract:0]
name = hillslope
type = layers
layers =
    s1_sample
containers =
    hillslope
exhaustive = True

[importlinter:contract:1]
name = hillslope.s1_sample
type = layers
layers =
    s2_inspect | s3_inspect | s4_inspect
containers =
    hillslope.s1_sample
exhaustive = True
"""
            )

        def test_multiple_packages_with_nesting(self, tmp_path: Path):
            # The logic here is that we want to have the minimum number of nesting
            # levels required to reach the minimum number of modules which is 3.

            # Arrange
            (tmp_path / ".importlinter").touch()
            (tmp_path / "hillslope").mkdir()
            (tmp_path / "hillslope" / "__init__.py").touch()
            (tmp_path / "hillslope" / "s1_sample").mkdir()
            (tmp_path / "hillslope" / "s1_sample" / "__init__.py").touch()
            (tmp_path / "hillslope" / "s1_sample" / "s2_inspect.py").touch()
            (tmp_path / "hillslope" / "s1_sample" / "s3_inspect.py").touch()
            (tmp_path / "hillslope" / "s1_sample" / "s4_inspect.py").touch()
            (tmp_path / "hillslope2").mkdir()
            (tmp_path / "hillslope2" / "__init__.py").touch()
            (tmp_path / "hillslope3").mkdir()
            (tmp_path / "hillslope3" / "__init__.py").touch()
            (tmp_path / "hillslope4").mkdir()
            (tmp_path / "hillslope4" / "__init__.py").touch()

            # Act
            with change_cwd(tmp_path), files_manager():
                use_import_linter()

            # Assert
            contents = (tmp_path / ".importlinter").read_text()
            assert contents == (
                """\
[importlinter]
root_packages =
    hillslope
    hillslope2
    hillslope3
    hillslope4

[importlinter:contract:0]
name = hillslope
type = layers
layers =
    s1_sample
containers =
    hillslope
exhaustive = True

[importlinter:contract:1]
name = hillslope.s1_sample
type = layers
layers =
    s2_inspect | s3_inspect | s4_inspect
containers =
    hillslope.s1_sample
exhaustive = True

[importlinter:contract:2]
name = hillslope2
type = layers
layers = 
containers =
    hillslope2
exhaustive = True

[importlinter:contract:3]
name = hillslope3
type = layers
layers = 
containers =
    hillslope3
exhaustive = True

[importlinter:contract:4]
name = hillslope4
type = layers
layers = 
containers =
    hillslope4
exhaustive = True
"""
            )

        def test_stdout_when_cant_find_package(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Having an issue where the message is being repeated multiple times
            # https://github.com/usethis-python/usethis-python/pull/501#issuecomment-2784482750

            # Act
            with change_cwd(tmp_path), files_manager(), usethis_config.set(frozen=True):
                use_import_linter()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Writing 'pyproject.toml'.\n"
                "✔ Adding dependency 'import-linter' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'import-linter'.\n"
                "⚠ Could not find any importable packages.\n"
                "⚠ Assuming the package name is test-stdout-when-cant-find-pac0.\n"
                "✔ Adding Import Linter config to 'pyproject.toml'.\n"
                "ℹ Ensure '__init__.py' files are used in your packages.\n"  # noqa: RUF001
                "ℹ For more info see <https://docs.python.org/3/tutorial/modules.html#packages>\n"  # noqa: RUF001
                "☐ Run 'uv run lint-imports' to run Import Linter.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_root_packages_not_added_if_already_root_package_ini(
            self, tmp_path: Path
        ):
            # Basically the user can either specify a list of root_packages, or
            # a single root package. We prefer to always use `root_packages`, but
            # we will leave the existing configuration alone if it already exists.

            # Arrange
            (tmp_path / ".importlinter").write_text(
                """\
[importlinter]
root_package = a
"""
            )

            # Act
            with change_cwd(tmp_path), files_manager():
                use_import_linter()

            # Assert
            contents = (tmp_path / ".importlinter").read_text()
            assert contents.startswith(
                """\
[importlinter]
root_package = a

[importlinter:contract:0]
"""
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_root_packages_not_added_if_already_root_package_toml(
            self, tmp_path: Path
        ):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
[tool.importlinter]
root_package = "a"
"""
            )

            # Act
            with change_cwd(tmp_path), files_manager():
                use_import_linter()

            # Assert
            content = (tmp_path / "pyproject.toml").read_text()
            assert "root_packages = " not in content
            assert "root_package = " in content

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_inp_rules_selected(self, tmp_path: Path):
            # Arrange
            (tmp_path / "ruff.toml").touch()

            with change_cwd(tmp_path), files_manager():
                # Act
                use_import_linter()

                # Assert
                assert "INP" in RuffTool().get_selected_rules()

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_inp_rules_not_selected_for_tests_dir(self, tmp_path: Path):
            # Arrange
            (tmp_path / "ruff.toml").touch()

            with change_cwd(tmp_path), files_manager():
                # Act
                use_import_linter()

            # Assert
            contents = (tmp_path / "ruff.toml").read_text()
            assert (
                contents
                == """\
[lint]
select = ["INP"]

[lint.per-file-ignores]
"*/tests/**" = ["INP"]
"""
            )

    class TestRemove:
        def test_config_file(self, uv_init_repo_dir: Path):
            # Arrange
            (uv_init_repo_dir / ".importlinter").touch()

            # Act
            with change_cwd(uv_init_repo_dir), files_manager():
                use_import_linter(remove=True)

            # Assert
            assert not (uv_init_repo_dir / ".importlinter").exists()

        def test_doesnt_add_pyproject(self, tmp_path: Path):
            # No pyproject.toml file to begin with...

            # Act
            with change_cwd(tmp_path), files_manager():
                use_import_linter(remove=True)

            # Assert
            assert not (tmp_path / "pyproject.toml").exists()

        def test_doesnt_deselect_inp_rules(self, tmp_path: Path):
            # Arrange
            (tmp_path / "ruff.toml").touch()

            with change_cwd(tmp_path), files_manager():
                RuffTool().select_rules(["INP"])

                # Act
                use_import_linter(remove=True)

            # Assert
            contents = (tmp_path / "ruff.toml").read_text()
            assert "INP" in contents

    class TestPreCommitIntegration:
        def test_config(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            (uv_init_repo_dir / ".pre-commit-config.yaml").write_text(
                """\
repos:
  - repo: local
    hooks:
      - id: placeholder
"""
            )

            # Act
            with change_cwd(uv_init_repo_dir), files_manager():
                use_import_linter()

            # Assert
            contents = (uv_init_repo_dir / ".pre-commit-config.yaml").read_text()
            assert "import-linter" in contents
            assert "placeholder" not in contents
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Adding dependency 'import-linter' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'import-linter'.\n"
                "✔ Adding Import Linter config to 'pyproject.toml'.\n"
                "✔ Adding hook 'import-linter' to '.pre-commit-config.yaml'.\n"
                "ℹ Ensure '__init__.py' files are used in your packages.\n"  # noqa: RUF001
                "ℹ For more info see <https://docs.python.org/3/tutorial/modules.html#packages>\n"  # noqa: RUF001
                "☐ Run 'uv run lint-imports' to run Import Linter.\n"
            )

    class TestBitbucketIntegration:
        def test_config_file(self, tmp_path: Path):
            # Arrange
            (tmp_path / "bitbucket-pipelines.yml").write_text("""\
image: atlassian/default-image:3
""")

            # Act
            with change_cwd(tmp_path), files_manager():
                use_import_linter()

            # Assert
            assert (tmp_path / "bitbucket-pipelines.yml").exists()
            contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
            assert "Import Linter" in contents
            assert "lint-imports" in contents
            assert "placeholder" not in contents


class TestPreCommit:
    class TestAdd:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_fresh(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_pre_commit()

                # Assert
                # Has dev dep
                (dev_dep,) = get_deps_from_group("dev")
                assert dev_dep == Dependency(name="pre-commit")
            # Correct stdout
            out, _ = capfd.readouterr()
            assert out == (
                "✔ Adding dependency 'pre-commit' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'pre-commit'.\n"
                "✔ Writing '.pre-commit-config.yaml'.\n"
                "✔ Adding placeholder hook to '.pre-commit-config.yaml'.\n"
                "☐ Remove the placeholder hook in '.pre-commit-config.yaml'.\n"
                "☐ Replace it with your own hooks.\n"
                "☐ Alternatively, use 'usethis tool' to add other tools and their hooks.\n"
                "☐ Run 'uv run pre-commit install' to register pre-commit.\n"
                "☐ Run 'uv run pre-commit run --all-files' to run the hooks manually.\n"
            )
            # Config file
            assert (uv_init_dir / ".pre-commit-config.yaml").exists()
            contents = (uv_init_dir / ".pre-commit-config.yaml").read_text()
            assert contents == (
                """\
repos:
  - repo: local
    hooks:
      - id: placeholder
        name: Placeholder - add your own hooks!
        entry: uv run --isolated --frozen --offline python -c "print('hello world!')"
        language: system
"""
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_config_file_already_exists(self, uv_init_repo_dir: Path):
            # Arrange
            (uv_init_repo_dir / ".pre-commit-config.yaml").write_text(
                """\
repos:
  - repo: local
    hooks:
      - id: my hook
        name: Its mine
        entry: uv run --isolated --frozen --offline python -c "print('hello world!')"
        language: system
"""
            )

            # Act
            with change_cwd(uv_init_repo_dir), files_manager():
                use_pre_commit()

            # Assert
            contents = (uv_init_repo_dir / ".pre-commit-config.yaml").read_text()
            assert contents == (
                """\
repos:
  - repo: local
    hooks:
      - id: my hook
        name: Its mine
        entry: uv run --isolated --frozen --offline python -c "print('hello world!')"
        language: system
"""
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_bad_commit(self, uv_env_dir: Path, git_path: Path):
            # This needs a venv so that we can actually run pre-commit via git

            # Arrange
            (uv_env_dir / ".gitignore").write_text(".venv/\n")

            # Act
            with change_cwd(uv_env_dir), files_manager():
                use_pre_commit()
            subprocess.run(
                [git_path.as_posix(), "add", "."], cwd=uv_env_dir, check=True
            )
            result = subprocess.run(
                [git_path.as_posix(), "commit", "-m", "Good commit"], cwd=uv_env_dir
            )
            assert not result.stderr
            assert result.returncode == 0, (
                f"stdout: {result.stdout}\nstderr: {result.stderr}\n"
            )

            # Assert
            (uv_env_dir / ".pre-commit-config.yaml").write_text("[")
            subprocess.run(
                [git_path.as_posix(), "add", "."], cwd=uv_env_dir, check=True
            )
            result = subprocess.run(
                [git_path.as_posix(), "commit", "-m", "Bad commit"],
                cwd=uv_env_dir,
                capture_output=True,
            )
            assert not result.stdout
            assert result.returncode != 0, (
                f"stdout: {result.stdout}\nstderr: {result.stderr}\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_requirements_txt_used(self, uv_init_dir: Path):
            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                with usethis_config.set(frozen=False):
                    use_requirements_txt()

                # Act
                use_pre_commit()

                # Assert
                assert "uv-export" in get_hook_ids()

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_pyproject_fmt_used(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_pyproject_fmt()

                # Act
                use_pre_commit()

                # Assert
                hook_names = get_hook_ids()
                assert "pyproject-fmt" in hook_names

                dev_deps = get_deps_from_group("dev")
                for dev_dep in dev_deps:
                    assert dev_dep.name != "pyproject-fmt"

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_codespell_used(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_codespell()

                # Act
                use_pre_commit()

                # Assert
                hook_names = get_hook_ids()
                assert "codespell" in hook_names

                dev_deps = get_deps_from_group("dev")
                for dep in dev_deps:
                    assert dep.name != "codespell"

    class TestRemove:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_config_file(self, uv_init_repo_dir: Path):
            # Arrange
            (uv_init_repo_dir / ".pre-commit-config.yaml").touch()

            # Act
            with change_cwd(uv_init_repo_dir), files_manager():
                use_pre_commit(remove=True)

            # Assert
            assert not (uv_init_repo_dir / ".pre-commit-config.yaml").exists()

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_dep(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                add_deps_to_group([Dependency(name="pre-commit")], "dev")

                # Act
                use_pre_commit(remove=True)

                # Assert
                assert not get_deps_from_group("dev")

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_stdout(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
            # Arrange
            (uv_init_dir / ".pre-commit-config.yaml").write_text(
                """\
repos:
  - repo: local
    hooks:
      - id: pre-commit
"""
            )

            with change_cwd(uv_init_dir), files_manager():
                # Arrange contd....
                # Add dependency
                add_deps_to_group([Dependency(name="pre-commit")], "dev")
                capfd.readouterr()

                # Act
                use_pre_commit(remove=True)

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "☐ Run 'uv run --with pre-commit pre-commit uninstall' to deregister pre-commit.\n"
                "✔ Removing '.pre-commit-config.yaml'.\n"
                "✔ Removing dependency 'pre-commit' from the 'dev' group in 'pyproject.toml'.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_requirements_txt_used(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                use_pre_commit()
                with usethis_config.set(frozen=False):
                    use_requirements_txt()
                capfd.readouterr()

                # Act
                use_pre_commit(remove=True)

                # Assert
                out, _ = capfd.readouterr()
                assert out.replace("\n", "") == (
                    "☐ Run 'uv run --with pre-commit pre-commit uninstall' to deregister pre-commit."
                    "✔ Removing '.pre-commit-config.yaml'."
                    "✔ Removing dependency 'pre-commit' from the 'dev' group in 'pyproject.toml'."
                    "☐ Run 'uv export --no-default-groups -o=requirements.txt' to write 'requirements.txt'."
                )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_pyproject_fmt_used(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                with usethis_config.set(quiet=True):
                    use_pre_commit()
                    use_pyproject_fmt()

                # Act
                use_pre_commit(remove=True)

                # Assert
                out, _ = capfd.readouterr()
                assert out == (
                    "☐ Run 'uv run --with pre-commit pre-commit uninstall' to deregister pre-commit.\n"
                    "✔ Removing '.pre-commit-config.yaml'.\n"
                    "✔ Removing dependency 'pre-commit' from the 'dev' group in 'pyproject.toml'.\n"
                    "✔ Adding dependency 'pyproject-fmt' to the 'dev' group in 'pyproject.toml'.\n"
                    "☐ Install the dependency 'pyproject-fmt'.\n"
                    "☐ Run 'uv run pyproject-fmt pyproject.toml' to run pyproject-fmt.\n"
                )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_codepsell_used(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                with usethis_config.set(quiet=True):
                    use_pre_commit()
                    use_codespell()
                    capfd.readouterr()

                # Act
                use_pre_commit(remove=True)

                # Assert
                out, err = capfd.readouterr()
                assert not err
                assert out == (
                    "☐ Run 'uv run --with pre-commit pre-commit uninstall' to deregister pre-commit.\n"
                    "✔ Removing '.pre-commit-config.yaml'.\n"
                    "✔ Removing dependency 'pre-commit' from the 'dev' group in 'pyproject.toml'.\n"
                    "✔ Adding dependency 'codespell' to the 'dev' group in 'pyproject.toml'.\n"
                    "☐ Install the dependency 'codespell'.\n"
                    "☐ Run 'uv run codespell' to run the Codespell spellchecker.\n"
                )

        def test_doesnt_add_pyproject(self, uv_init_repo_dir: Path):
            # Arrange
            # We use uv_init_repo_dir to get a git repo
            (uv_init_repo_dir / "pyproject.toml").unlink()

            # Act
            with change_cwd(uv_init_repo_dir), files_manager():
                use_pre_commit(remove=True)

            # Assert
            assert not (uv_init_repo_dir / "pyproject.toml").exists()

    class TestBitbucketCIIntegration:
        def test_prexisting(self, uv_init_repo_dir: Path):
            # Arrange
            (uv_init_repo_dir / "bitbucket-pipelines.yml").write_text(
                """\
image: atlassian/default-image:3
"""
            )

            with change_cwd(uv_init_repo_dir), files_manager():
                # Act
                use_pre_commit()

            # Assert
            contents = (uv_init_repo_dir / "bitbucket-pipelines.yml").read_text()
            assert "pre-commit" in contents

        def test_remove(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
            # Arrange
            with change_cwd(uv_init_dir), files_manager():
                use_pre_commit()
            capfd.readouterr()
            (uv_init_dir / "bitbucket-pipelines.yml").write_text(
                """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Run pre-commit
            script:
              - echo "Hello, World!"
"""
            )

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_pre_commit(remove=True)

            # Assert
            contents = (uv_init_dir / "bitbucket-pipelines.yml").read_text()
            assert (
                contents
                == """\
image: atlassian/default-image:3
definitions:
    caches:
        uv: ~/.cache/uv
    script_items:
      - &install-uv |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.local/bin/env
        export UV_LINK_MODE=copy
        uv --version
pipelines:
    default:
      - step:
            name: Placeholder - add your own steps!
            caches:
              - uv
            script:
              - *install-uv
              - echo 'Hello, world!'
"""
            )
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Removing 'Run pre-commit' from default pipeline in 'bitbucket-pipelines.yml'.\n"
                "✔ Adding cache 'uv' definition to 'bitbucket-pipelines.yml'.\n"
                "☐ Run 'uv run --with pre-commit pre-commit uninstall' to deregister pre-commit.\n"
                "✔ Removing '.pre-commit-config.yaml'.\n"
                "✔ Removing dependency 'pre-commit' from the 'dev' group in 'pyproject.toml'.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_remove_subsumed_tools(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_ci_bitbucket()
                # other tools moved to pre-commit, which should be removed
                use_deptry()
                use_ruff()

                # Act
                use_pre_commit()

            # Assert
            contents = (uv_init_repo_dir / "bitbucket-pipelines.yml").read_text()
            assert "pre-commit" in contents
            assert "deptry" not in contents
            assert "ruff" not in contents

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_add_unsubsumed_tools(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_ci_bitbucket()
                use_pre_commit()
                # other tools moved from pre-commit, which should be added
                use_deptry()
                use_ruff()

                # Act
                use_pre_commit(remove=True)

            # Assert
            contents = (uv_init_repo_dir / "bitbucket-pipelines.yml").read_text()
            assert "pre-commit" not in contents
            assert "deptry" in contents
            assert "ruff" in contents

    class TestMultipleIntegrations:
        def test_hooks_run_all_tools_empty_repo(self, uv_env_dir: Path):
            # Arrange
            with change_cwd(uv_env_dir), files_manager():
                # Add the tools
                use_pre_commit()
                for tool in ALL_TOOLS:
                    if tool.get_pre_commit_repos():
                        use_tool(tool)

                # Act, Assert
                # Run the pre-commit hooks via subprocess - check it doesn't raise
                call_uv_subprocess(
                    ["run", "pre-commit", "run", "--all-files"],
                    change_toml=False,
                )


class TestPyprojectFmt:
    class TestAdd:
        class TestPyproject:
            @pytest.mark.usefixtures("_vary_network_conn")
            def test_added(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
                # Arrange
                with (
                    change_cwd(uv_init_dir),
                    PyprojectTOMLManager(),
                    usethis_config.set(quiet=True),
                ):
                    add_deps_to_group([Dependency(name="pyproject-fmt")], "dev")

                # Act
                with change_cwd(uv_init_dir), PyprojectTOMLManager():
                    use_pyproject_fmt()

                # Assert
                assert (
                    (uv_init_dir / "pyproject.toml")
                    .read_text()
                    .__contains__(
                        """\
[tool.pyproject-fmt]
keep_full_version = true
"""
                    )
                )
                out, _ = capfd.readouterr()
                assert out == (
                    "✔ Adding pyproject-fmt config to 'pyproject.toml'.\n"
                    "☐ Run 'uv run pyproject-fmt pyproject.toml' to run pyproject-fmt.\n"
                )

        class TestDeps:
            @pytest.mark.usefixtures("_vary_network_conn")
            def test_added(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
                with change_cwd(uv_init_dir), PyprojectTOMLManager():
                    # Act
                    use_pyproject_fmt()

                    # Assert
                    assert get_deps_from_group("dev") == [
                        Dependency(name="pyproject-fmt")
                    ]
                out, _ = capfd.readouterr()
                assert out == (
                    "✔ Adding dependency 'pyproject-fmt' to the 'dev' group in 'pyproject.toml'.\n"
                    "☐ Install the dependency 'pyproject-fmt'.\n"
                    "✔ Adding pyproject-fmt config to 'pyproject.toml'.\n"
                    "☐ Run 'uv run pyproject-fmt pyproject.toml' to run pyproject-fmt.\n"
                )

        def test_bitbucket_integration(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            with change_cwd(uv_init_dir), files_manager():
                use_ci_bitbucket()
                capfd.readouterr()

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_pyproject_fmt()

            # Assert
            assert (
                "pyproject-fmt" in (uv_init_dir / "bitbucket-pipelines.yml").read_text()
            )
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Adding dependency 'pyproject-fmt' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'pyproject-fmt'.\n"
                "✔ Adding 'Run pyproject-fmt' to default pipeline in 'bitbucket-pipelines.yml'.\n"
                "✔ Adding pyproject-fmt config to 'pyproject.toml'.\n"
                "☐ Run 'uv run pyproject-fmt pyproject.toml' to run pyproject-fmt.\n"
            )

    class TestRemove:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_config_file(self, uv_init_dir: Path):
            # Arrange
            (uv_init_dir / "pyproject.toml").write_text(
                """\
[tool.pyproject-fmt]
foo = "bar"
"""
            )

            # Act
            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                use_pyproject_fmt(remove=True)

            # Assert
            assert (uv_init_dir / "pyproject.toml").read_text() == ""

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_bitbucket_integration(self, uv_init_dir: Path):
            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                use_ci_bitbucket()
                use_pyproject_fmt()

                # Act
                use_pyproject_fmt(remove=True)

            # Assert
            contents = (uv_init_dir / "bitbucket-pipelines.yml").read_text()
            assert "pyproject-fmt" not in contents

        def test_doesnt_add_pyproject(self, tmp_path: Path):
            # No pyproject.toml file to begin with...

            # Act
            with change_cwd(tmp_path), files_manager():
                use_pyproject_fmt(remove=True)

            # Assert
            assert not (tmp_path / "pyproject.toml").exists()

    class TestPreCommitIntegration:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_use_first(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_pre_commit()

                # Act
                use_pyproject_fmt()

                # Assert
                hook_names = get_hook_ids()

            assert (uv_init_repo_dir / ".pre-commit-config.yaml").exists()
            assert "pyproject-fmt" in hook_names

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_use_after(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_pyproject_fmt()

                # Act
                use_pre_commit()

                # Assert
                hook_names = get_hook_ids()

            assert (uv_init_repo_dir / ".pre-commit-config.yaml").exists()
            assert "pyproject-fmt" in hook_names

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_remove_with_precommit(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                with usethis_config.set(quiet=True):
                    use_pyproject_fmt()
                    use_pre_commit()

                # Act
                use_pyproject_fmt(remove=True)

            # Assert
            contents = (uv_init_repo_dir / ".pre-commit-config.yaml").read_text()
            assert "pyproject-fmt" not in contents
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Removing pyproject-fmt config from 'pyproject.toml'.\n"
                "✔ Removing hook 'pyproject-fmt' from '.pre-commit-config.yaml'.\n"
            )
            # N.B. we don't remove it as a dependency because it's not a dep when
            # pre-commit is used.

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_remove_without_precommit(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_repo_dir), PyprojectTOMLManager():
                # Arrange
                with usethis_config.set(quiet=True):
                    use_pyproject_fmt()

                # Act
                use_pyproject_fmt(remove=True)

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Removing pyproject-fmt config from 'pyproject.toml'.\n"
                "✔ Removing dependency 'pyproject-fmt' from the 'dev' group in 'pyproject.toml'.\n"
            )


class TestPyprojectTOML:
    class TestRemove:
        def test_doesnt_invoke_ensure_pyproject_toml(self, tmp_path: Path):
            # Arrange
            # Mock the ensure_pyproject_toml function to raise an error

            mock = MagicMock()

            # Act
            with (
                unittest.mock.patch("usethis._core.tool.ensure_pyproject_toml", mock),
                change_cwd(tmp_path),
                files_manager(),
            ):
                use_pyproject_toml(remove=True)

            # Assert
            assert not mock.called
            assert not (tmp_path / "pyproject.toml").exists()


class TestPytest:
    class TestAdd:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_no_pyproject(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
            with change_cwd(tmp_path), files_manager():
                # Act
                use_pytest()

                # Assert
                deps_from_test = get_deps_from_group("test")
                assert is_dep_satisfied_in(
                    Dependency(name="pytest"), in_=list(deps_from_test)
                )
                # pytest-cov should only be added when we are using coverage
                assert not is_dep_satisfied_in(
                    Dependency(name="pytest-cov"), in_=list(deps_from_test)
                )
                out, _ = capfd.readouterr()
                assert out == (
                    "✔ Writing 'pyproject.toml'.\n"
                    "✔ Adding dependency 'pytest' to the 'test' group in 'pyproject.toml'.\n"
                    "✔ Adding pytest config to 'pyproject.toml'.\n"
                    "✔ Creating '/tests'.\n"
                    "✔ Writing '/tests/conftest.py'.\n"
                    "☐ Add test files to the '/tests' directory with the format 'test_*.py'.\n"
                    "☐ Add test functions with the format 'test_*()'.\n"
                    "☐ Run 'uv run pytest' to run the tests.\n"
                )

            assert (tmp_path / "pyproject.toml").exists()
            content = (tmp_path / "pyproject.toml").read_text()
            assert content.__contains__(
                """\
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--import-mode=importlib", "-ra", "--strict-markers", "--strict-config"]
filterwarnings = ["error"]
xfail_strict = true
log_cli_level = "INFO"
minversion = "7\""""
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_bitbucket_integration(self, uv_init_dir: Path):
            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                use_ci_bitbucket()

                # Act
                use_pytest()

            # Assert
            assert "pytest" in (uv_init_dir / "bitbucket-pipelines.yml").read_text()

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_coverage_integration(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                with usethis_config.set(quiet=True):
                    use_coverage_py()

                # Act
                use_pytest()

            # Assert
            out, _ = capfd.readouterr()
            assert out == (
                "✔ Adding dependencies 'pytest', 'pytest-cov' to the 'test' group in \n'pyproject.toml'.\n"
                "☐ Install the dependencies 'pytest', 'pytest-cov'.\n"
                "✔ Adding pytest config to 'pyproject.toml'.\n"
                "✔ Creating '/tests'.\n"
                "✔ Writing '/tests/conftest.py'.\n"
                "☐ Add test files to the '/tests' directory with the format 'test_*.py'.\n"
                "☐ Add test functions with the format 'test_*()'.\n"
                "☐ Run 'uv run pytest' to run the tests.\n"
                "☐ Run 'uv run pytest --cov' to run your tests with Coverage.py.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_pytest_installed(self, tmp_path: Path):
            with change_cwd(tmp_path), files_manager():
                # Act
                use_pytest()

                # Assert
                # This will raise if pytest is not installed
                call_uv_subprocess(["pip", "show", "pytest"], change_toml=False)

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_registers_test_group(self, tmp_path: Path):
            with change_cwd(tmp_path), files_manager():
                # Act
                use_pytest()

                # Assert
                default_groups = PyprojectTOMLManager()[
                    ["tool", "uv", "default-groups"]
                ]
                assert "test" in default_groups

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_registers_test_group_uv_toml(self, tmp_path: Path):
            with change_cwd(tmp_path), files_manager():
                # Arrange
                (tmp_path / "uv.toml").touch()

                # Act
                use_pytest()

                # Assert
                default_groups = UVTOMLManager()[["default-groups"]]
                assert "test" in default_groups

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_ruff_integration(self, uv_init_dir: Path):
            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                use_ruff()

                # Act
                use_pytest()

                # Assert
                assert "PT" in RuffTool().get_selected_rules()

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_pytest_ini_priority(self, uv_init_dir: Path):
            # Arrange
            (uv_init_dir / "pytest.ini").touch()
            (uv_init_dir / "uv.lock").touch()

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_pytest()

            # Assert
            assert (
                (uv_init_dir / "pytest.ini").read_text()
                == """\
[pytest]
testpaths =
    tests
addopts =
    --import-mode=importlib
    -ra
    --strict-markers
    --strict-config
filterwarnings =
    error
xfail_strict = True
log_cli_level = INFO
minversion = 7
"""
            )

            with PyprojectTOMLManager() as manager:
                assert ["tool", "pytest"] not in manager

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_pyproject_with_ini_priority(self, uv_init_repo_dir: Path):
            # testing it takes priority over setup.cfg
            # Arrange
            (uv_init_repo_dir / "setup.cfg").touch()
            (uv_init_repo_dir / "pyproject.toml").write_text("""\
[tool.pytest.ini_options]
testpaths = ["tests"]
""")

            # Act
            with change_cwd(uv_init_repo_dir), files_manager():
                use_pytest()

            # Assert
            assert (uv_init_repo_dir / "setup.cfg").read_text() == "", (
                "Expected pyproject.toml to take priority when it has a [tool.pytest.ini_options] section"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_pyproject_without_ini_priority(self, uv_init_repo_dir: Path):
            # Arrange
            (uv_init_repo_dir / "setup.cfg").touch()
            (uv_init_repo_dir / "pyproject.toml").write_text("""\
[tool.pytest]
foo = "bar"
""")

            # Act
            with change_cwd(uv_init_repo_dir), files_manager():
                use_pytest()

            # Assert
            assert (uv_init_repo_dir / "setup.cfg").read_text()

        def test_pythonpath_needed(self, tmp_path: Path):
            # https://github.com/usethis-python/usethis-python/issues/347

            # Arrange
            # No build backend, so finding './src' for imports won't work unless we
            # explicitly tell pytest where to go.
            (tmp_path / "pyproject.toml").touch()

            (tmp_path / "src").mkdir()
            (tmp_path / "src" / "foo").mkdir()
            (tmp_path / "src" / "foo" / "__init__.py").touch()

            (tmp_path / "tests").mkdir()
            (tmp_path / "tests" / "test_foo.py").write_text(
                """\
def test_foo():
    import foo
"""
            )

            # Act
            with change_cwd(tmp_path), files_manager():
                use_pytest()

            with change_cwd(tmp_path):
                # Assert (that this doesn't raise an error)
                call_uv_subprocess(["run", "pytest"], change_toml=False)

    class TestRemove:
        class TestRuffIntegration:
            def test_deselected(self, uv_init_dir: Path):
                # Arrange
                (uv_init_dir / "pyproject.toml").write_text(
                    """\
[tool.ruff.lint]
select = ["E", "PT"]
"""
                )

                # Act
                with change_cwd(uv_init_dir), files_manager():
                    use_pytest(remove=True)

                # Assert
                assert (uv_init_dir / "pyproject.toml").read_text() == (
                    """\
[tool.ruff.lint]
select = ["E"]
"""
                )

            def test_message(
                self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
            ):
                # Arrange
                (uv_init_dir / "pyproject.toml").write_text(
                    """\
[tool.ruff.lint]
select = ["PT"]
"""
                )

                # Act
                with change_cwd(uv_init_dir), files_manager():
                    use_pytest(remove=True)

                # Assert
                out, _ = capfd.readouterr()
                assert (
                    out
                    == """\
✔ Deselecting Ruff rule 'PT' in 'pyproject.toml'.
"""
                )

        class TestPyprojectIntegration:
            def test_removed(
                self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
            ):
                # Arrange
                (uv_init_dir / "pyproject.toml").write_text(
                    """\
    [tool.pytest]
    foo = "bar"
    """
                )

                # Act
                with change_cwd(uv_init_dir), files_manager():
                    use_pytest(remove=True)

                # Assert
                assert (uv_init_dir / "pyproject.toml").read_text() == ""
                out, _ = capfd.readouterr()
                # N.B. we don't put `pytest` in quotes because we are referring to the
                # tool, not the package.
                assert out == "✔ Removing pytest config from 'pyproject.toml'.\n"

        class TestDependencies:
            def test_removed(self, uv_init_dir: Path):
                with change_cwd(uv_init_dir), files_manager():
                    # Arrange
                    add_deps_to_group([Dependency(name="pytest")], "test")

                    # Act
                    use_pytest(remove=True)

                    # Assert
                    assert not get_deps_from_group("test")

        class TestBitbucketIntegration:
            def test_remove(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
                # Arrange
                with (
                    change_cwd(uv_init_dir),
                    files_manager(),
                    usethis_config.set(quiet=True),
                ):
                    use_pytest()

                (uv_init_dir / "bitbucket-pipelines.yml").write_text(
                    """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Test on 3.12
            script:
              - uv run --python 3.12 pytest -x --junitxml=test-reports/report.xml
"""
                )

                # Act
                with change_cwd(uv_init_dir), files_manager():
                    use_pytest(remove=True)

                # Assert
                contents = (uv_init_dir / "bitbucket-pipelines.yml").read_text()
                assert (
                    contents
                    == """\
image: atlassian/default-image:3
definitions:
    caches:
        uv: ~/.cache/uv
    script_items:
      - &install-uv |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.local/bin/env
        export UV_LINK_MODE=copy
        uv --version
pipelines:
    default:
      - step:
            name: Placeholder - add your own steps!
            caches:
              - uv
            script:
              - *install-uv
              - echo 'Hello, world!'
"""
                )
                out, err = capfd.readouterr()
                assert not err
                assert out.replace("\n", "").replace(" ", "") == (
                    "✔ Removing 'Test on 3.12' from default pipeline in 'bitbucket-pipelines.yml'.\n"
                    "✔ Adding cache 'uv' definition to 'bitbucket-pipelines.yml'.\n"
                    "✔ Removing pytest config from 'pyproject.toml'.\n"
                    "✔ Removing dependency 'pytest' from the 'test' group in 'pyproject.toml'.\n"
                    "✔ Removing '/tests'.\n"
                ).replace("\n", "").replace(" ", "")

        def test_coverage_integration(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_dir), files_manager():
                # Arrange
                with usethis_config.set(quiet=True):
                    use_coverage_py()
                    use_pytest()

                # Act
                use_pytest(remove=True)

            # Assert
            out, _ = capfd.readouterr()
            assert out == (
                "✔ Removing pytest config from 'pyproject.toml'.\n"
                "✔ Removing dependencies 'pytest', 'pytest-cov' from the 'test' group in \n'pyproject.toml'.\n"
                "✔ Removing '/tests'.\n"
                "☐ Run 'uv run coverage help' to see available Coverage.py commands.\n"
            )

        def test_doesnt_create_pyproject_toml(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").unlink(missing_ok=True)

            # Act
            with change_cwd(tmp_path), files_manager():
                use_pytest(remove=True)

            # Assert
            assert not (tmp_path / "pyproject.toml").exists()


class TestRequirementsTxt:
    class TestAdd:
        def test_start_from_nothing(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                use_requirements_txt()

            # Assert
            assert (tmp_path / "requirements.txt").exists()
            out, err = capfd.readouterr()
            assert not err
            assert out.replace("\n", "") == (
                "✔ Writing 'pyproject.toml'."
                "✔ Writing 'uv.lock'."
                "✔ Writing 'requirements.txt'."
                "☐ Run 'uv export --no-default-groups -o=requirements.txt' to write 'requirements.txt'."
            )

        def test_start_from_uv_init(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with (
                change_cwd(uv_init_dir),
                PyprojectTOMLManager(),
                usethis_config.set(frozen=False),
            ):
                use_requirements_txt()

            # Assert
            assert (uv_init_dir / "requirements.txt").exists()
            out, err = capfd.readouterr()
            assert not err
            assert out.replace("\n", "") == (
                "✔ Writing 'uv.lock'."
                "✔ Writing 'requirements.txt'."
                "☐ Run 'uv export --no-default-groups -o=requirements.txt' to write 'requirements.txt'."
            )

        def test_start_from_uv_locked(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with (
                change_cwd(uv_init_dir),
                PyprojectTOMLManager(),
                usethis_config.set(frozen=False),
            ):
                # Arrange
                call_uv_subprocess(["lock"], change_toml=False)

                # Act
                use_requirements_txt()

            # Assert
            assert (uv_init_dir / "requirements.txt").exists()
            out, err = capfd.readouterr()
            assert not err
            assert out.replace("\n", "") == (
                "✔ Writing 'requirements.txt'."
                "☐ Run 'uv export --no-default-groups -o=requirements.txt' to write 'requirements.txt'."
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_pre_commit(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with (
                change_cwd(uv_init_repo_dir),
                files_manager(),
                usethis_config.set(frozen=False),
            ):
                # Arrange
                use_pre_commit()
                capfd.readouterr()

                # Act
                use_requirements_txt()

            # Assert
            assert (uv_init_repo_dir / "requirements.txt").exists()
            content = (uv_init_repo_dir / ".pre-commit-config.yaml").read_text()
            assert content == (
                """\
repos:
  - repo: local
    hooks:
      - id: uv-export
        name: uv-export
        files: ^uv\\.lock$
        entry: uv export --frozen --offline --quiet --no-default-groups -o=requirements.txt
        language: system
        pass_filenames: false
        require_serial: true
"""
            )
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Adding hook 'uv-export' to '.pre-commit-config.yaml'.\n"
                "✔ Writing 'requirements.txt'.\n"
                "☐ Run 'uv run pre-commit run uv-export' to write 'requirements.txt'.\n"
            )

    class TestRemove:
        def test_file_gone(self, tmp_path: Path):
            # Arrange
            (tmp_path / "requirements.txt").touch()

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                use_requirements_txt(remove=True)

            # Assert
            assert not (tmp_path / "requirements.txt").exists()

        def test_requirements_dir(self, tmp_path: Path):
            # Arrange
            (tmp_path / "requirements.txt").mkdir()

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                use_requirements_txt(remove=True)

            # Assert
            assert (tmp_path / "requirements.txt").exists()

        def test_precommit_integration(self, tmp_path: Path):
            # Arrange
            (tmp_path / ".pre-commit-config.yaml").write_text(
                """\
repos:
  - repo: local
    hooks:
      - id: uv-export
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                use_requirements_txt(remove=True)

            # Assert
            assert (tmp_path / ".pre-commit-config.yaml").exists()
            content = (tmp_path / ".pre-commit-config.yaml").read_text()
            assert "uv-export" not in content

        def test_roundtrip(self, tmp_path: Path):
            with change_cwd(tmp_path), PyprojectTOMLManager():
                # Arrange
                use_requirements_txt()

                # Act
                use_requirements_txt(remove=True)

            # Assert
            assert not (tmp_path / "requirements.txt").exists()

        def test_doesnt_create_pyproject_toml(self, tmp_path: Path):
            # Act
            with change_cwd(tmp_path), files_manager():
                use_requirements_txt(remove=True)

            # Assert
            assert not (tmp_path / "pyproject.toml").exists()


class TestRuff:
    class TestAdd:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_dependency_added(self, uv_init_dir: Path):
            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff()

                # Assert
                (dev_dep,) = get_deps_from_group("dev")
            assert dev_dep == Dependency(name="ruff")

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_stdout(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff()

            # Assert
            out, _ = capfd.readouterr()
            assert out == (
                "✔ Adding dependency 'ruff' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'ruff'.\n"
                "✔ Adding Ruff config to 'pyproject.toml'.\n"
                "✔ Selecting Ruff rules 'A', 'C4', 'E4', 'E7', 'E9', 'F', 'FLY', 'FURB', 'I', \n'PLE', 'PLR', 'RUF', 'SIM', 'UP' in 'pyproject.toml'.\n"
                "✔ Ignoring Ruff rules 'PLR2004', 'SIM108' in 'pyproject.toml'.\n"
                "☐ Run 'uv run ruff check --fix' to run the Ruff linter with autofixes.\n"
                "☐ Run 'uv run ruff format' to run the Ruff formatter.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_pre_commit_first(self, uv_init_repo_dir: Path):
            # Act
            with change_cwd(uv_init_repo_dir), files_manager():
                use_ruff()
                use_pre_commit()

                # Assert
                hook_names = get_hook_ids()

            assert "ruff-format" in hook_names
            assert "ruff" in hook_names

        def test_creates_pyproject_toml(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(tmp_path), files_manager():
                use_ruff()

            # Assert
            assert (tmp_path / "pyproject.toml").exists()
            out, err = capfd.readouterr()
            assert not err
            assert out.startswith("✔ Writing 'pyproject.toml'.\n")

        def test_existing_ruff_toml(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # https://github.com/usethis-python/usethis-python/issues/420

            # Arrange
            (uv_init_dir / "ruff.toml").write_text("""\
namespace-packages = ["src/usethis/namespace"]

[lint]
select = [ "ALL" ]
ignore = [ "EM", "T20", "TRY003", "S603" ]

[lint.extend-per-file-ignores]
"__main__.py" = [ "BLE001" ]
""")

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Adding dependency 'ruff' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'ruff'.\n"
                "✔ Adding Ruff config to 'ruff.toml'.\n"
                "☐ Run 'uv run ruff check --fix' to run the Ruff linter with autofixes.\n"
                "☐ Run 'uv run ruff format' to run the Ruff formatter.\n"
            )
            assert (uv_init_dir / "ruff.toml").read_text() == (
                """\
namespace-packages = ["src/usethis/namespace"]
line-length = 88

[lint]
select = [ "ALL" ]
ignore = [ "EM", "T20", "TRY003", "S603" ]

[lint.extend-per-file-ignores]
"__main__.py" = [ "BLE001" ]

[format]
docstring-code-format = true
"""
            )

        def test_doesnt_overwrite_existing_line_length(self, uv_init_dir: Path):
            # Arrange
            (uv_init_dir / "ruff.toml").write_text("line-length = 100")

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff()

                # Assert
                assert RuffTOMLManager()[["line-length"]] == 100

        def test_only_add_linter(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff(linter=True, formatter=False)

                # Assert
                assert not PyprojectTOMLManager().__contains__(
                    ["tool", "ruff", "format"]
                )

            out, _ = capfd.readouterr()
            assert out == (
                "✔ Adding dependency 'ruff' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'ruff'.\n"
                "✔ Adding Ruff config to 'pyproject.toml'.\n"
                "✔ Selecting Ruff rules 'A', 'C4', 'E4', 'E7', 'E9', 'F', 'FLY', 'FURB', 'I', \n'PLE', 'PLR', 'RUF', 'SIM', 'UP' in 'pyproject.toml'.\n"
                "✔ Ignoring Ruff rules 'PLR2004', 'SIM108' in 'pyproject.toml'.\n"
                "☐ Run 'uv run ruff check --fix' to run the Ruff linter with autofixes.\n"
            )

        def test_only_add_formatter(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff(linter=False, formatter=True)

                # Assert
                assert not PyprojectTOMLManager().__contains__(["tool", "ruff", "lint"])

            out, _ = capfd.readouterr()
            assert out == (
                "✔ Adding dependency 'ruff' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'ruff'.\n"
                "✔ Adding Ruff config to 'pyproject.toml'.\n"
                "☐ Run 'uv run ruff format' to run the Ruff formatter.\n"
            )

    class TestRemove:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_config_file(self, uv_init_dir: Path):
            # Arrange
            (uv_init_dir / "pyproject.toml").write_text(
                """\
[tool.ruff.lint]
select = ["A", "B", "C"]
"""
            )

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff(remove=True)

            # Assert
            assert (uv_init_dir / "pyproject.toml").read_text() == ""

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_blank_slate(self, uv_init_dir: Path):
            # Arrange
            contents = (uv_init_dir / "pyproject.toml").read_text()

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff(remove=True)

            # Assert
            assert (uv_init_dir / "pyproject.toml").read_text() == contents

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_roundtrip(self, uv_init_dir: Path):
            # Arrange
            with change_cwd(uv_init_dir), files_manager():
                ensure_symlink_mode()
            contents = (uv_init_dir / "pyproject.toml").read_text()

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff()
                use_ruff(remove=True)

            # Assert
            assert (
                (uv_init_dir / "pyproject.toml").read_text()
                == contents
                + """\

[dependency-groups]
dev = []
"""
            )

        def test_doesnt_create_pyproject_toml(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").unlink(missing_ok=True)

            # Act
            with change_cwd(tmp_path), files_manager():
                use_ruff(remove=True)

            # Assert
            assert not (tmp_path / "pyproject.toml").exists()

        def test_only_formatter(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
[tool.ruff.lint]
select = ["E", "PT"]

[tool.ruff.format]
select = ["F"]
"""
            )

            # Act
            with change_cwd(tmp_path), files_manager():
                use_ruff(linter=False, formatter=True, remove=True)

            # Assert
            assert (tmp_path / "pyproject.toml").read_text() == (
                """\
[tool.ruff.lint]
select = ["E", "PT"]

"""
            )

        def test_only_linter(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
[tool.ruff.lint]
fake = ["E", "PT"]

[tool.ruff.format]
select = ["F"]
"""
            )

            # Act
            with change_cwd(tmp_path), files_manager():
                use_ruff(linter=True, formatter=False, remove=True)

            # Assert
            assert (tmp_path / "pyproject.toml").read_text() == (
                """\
[tool.ruff.format]
select = ["F"]
"""
            )

    class TestHow:
        def test_both_linter_and_formatter(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff(how=True, linter=True, formatter=True)

            # Assert
            out, _ = capfd.readouterr()
            assert out == (
                "☐ Run 'ruff check --fix' to run the Ruff linter with autofixes.\n"
                "☐ Run 'ruff format' to run the Ruff formatter.\n"
            )

        def test_only_linter(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff(how=True, linter=True, formatter=False)

            # Assert
            out, _ = capfd.readouterr()
            assert out == (
                "☐ Run 'ruff check --fix' to run the Ruff linter with autofixes.\n"
            )

        def test_only_formatter(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(uv_init_repo_dir), files_manager():
                use_ruff(how=True, linter=False, formatter=True)

            # Assert
            out, _ = capfd.readouterr()
            assert out == "☐ Run 'ruff format' to run the Ruff formatter.\n"

    class TestPrecommitIntegration:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_use_first(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_ruff()

                # Act
                use_pre_commit()

                # Assert
                hook_names = get_hook_ids()

            assert "ruff-format" in hook_names
            assert "ruff" in hook_names

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_use_after(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_pre_commit()

                # Act
                use_ruff()

                # Assert
                hook_names = get_hook_ids()

            assert "ruff-format" in hook_names
            assert "ruff" in hook_names

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_remove(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                with usethis_config.set(quiet=True):
                    use_ruff()
                    use_pre_commit()

                # Act
                use_ruff(remove=True)

            # Assert
            contents = (uv_init_repo_dir / ".pre-commit-config.yaml").read_text()
            assert "ruff" not in contents
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Removing hook 'ruff' from '.pre-commit-config.yaml'.\n"
                "✔ Removing hook 'ruff-format' from '.pre-commit-config.yaml'.\n"
                "✔ Removing Ruff config from 'pyproject.toml'.\n"
                "✔ Removing dependency 'ruff' from the 'dev' group in 'pyproject.toml'.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_add_only_linter(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_pre_commit()
                capfd.readouterr()

                # Act
                use_ruff(linter=True, formatter=False)

                # Assert
                hook_names = get_hook_ids()

            # 1. File exists
            assert (uv_init_repo_dir / ".pre-commit-config.yaml").exists()

            # 2. Hook is in the file
            assert "ruff" in hook_names
            assert "ruff-format" not in hook_names

            # 3. Test file contents
            assert (uv_init_repo_dir / ".pre-commit-config.yaml").read_text() == (
                """\
repos:
  - repo: local
    hooks:
      - id: ruff
        name: ruff
        types_or:
          - python
          - pyi
          - jupyter
        always_run: true
        entry: uv run --frozen --offline ruff check --fix --force-exclude
        language: system
        require_serial: true
"""
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_add_only_linter_to_existing_formatter(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_ruff(formatter=True)
                use_pre_commit()
                capfd.readouterr()

                # Act
                use_ruff(linter=True, formatter=False)

                # Assert
                hook_names = get_hook_ids()

            # 1. File exists
            assert (uv_init_repo_dir / ".pre-commit-config.yaml").exists()

            # 2. Hook is in the file
            assert "ruff" in hook_names
            assert "ruff-format" in hook_names

            # 3. Test file contents
            assert (uv_init_repo_dir / ".pre-commit-config.yaml").read_text() == (
                """\
repos:
  - repo: local
    hooks:
      - id: ruff
        name: ruff
        types_or:
          - python
          - pyi
          - jupyter
        always_run: true
        entry: uv run --frozen --offline ruff check --fix --force-exclude
        language: system
        require_serial: true
  - repo: local
    hooks:
      - id: ruff-format
        name: ruff-format
        types_or:
          - python
          - pyi
          - jupyter
        always_run: true
        entry: uv run --frozen --offline ruff format --force-exclude
        language: system
        require_serial: true
"""
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_add_only_formatter(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_pre_commit()
                capfd.readouterr()

                # Act
                use_ruff(linter=False, formatter=True)

                # Assert
                hook_names = get_hook_ids()

            # 1. File exists
            assert (uv_init_repo_dir / ".pre-commit-config.yaml").exists()

            # 2. Hook is in the file
            assert "ruff" not in hook_names
            assert "ruff-format" in hook_names

            # 3. Test file contents
            assert (uv_init_repo_dir / ".pre-commit-config.yaml").read_text() == (
                """\
repos:
  - repo: local
    hooks:
      - id: ruff-format
        name: ruff-format
        types_or:
          - python
          - pyi
          - jupyter
        always_run: true
        entry: uv run --frozen --offline ruff format --force-exclude
        language: system
        require_serial: true
"""
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_remove_only_linter(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_repo_dir), files_manager():
                # Arrange
                use_ruff()
                use_pre_commit()
                capfd.readouterr()

                # Act
                use_ruff(linter=True, formatter=False, remove=True)

                # Assert
                hook_names = get_hook_ids()

            # 1. File exists
            assert (uv_init_repo_dir / ".pre-commit-config.yaml").exists()

            # 2. Hook is in the file
            assert "ruff" not in hook_names
            assert "ruff-format" in hook_names

            # 3. Test file contents
            assert (uv_init_repo_dir / ".pre-commit-config.yaml").read_text() == (
                """\
repos:
  - repo: local
    hooks:
      - id: ruff-format
        name: ruff-format
        types_or:
          - python
          - pyi
          - jupyter
        always_run: true
        entry: uv run --frozen --offline ruff format --force-exclude
        language: system
        require_serial: true
"""
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_remove_only_linter_yaml_only(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            (uv_init_repo_dir / ".pre-commit-config.yaml").write_text("""\
repos:
  - repo: local
    hooks:
      - id: ruff
        name: ruff
        types_or:
          - python
          - pyi
          - jupyter
        always_run: true
        entry: uv run --frozen --offline ruff check --fix --force-exclude
        language: system
        require_serial: true
  - repo: local
    hooks:
      - id: ruff-format
        name: ruff-format
        types_or:
          - python
          - pyi
          - jupyter
        always_run: true
        entry: uv run --frozen --offline ruff format --force-exclude
        language: system
        require_serial: true
""")

            with change_cwd(uv_init_repo_dir), files_manager():
                capfd.readouterr()

                # Act
                use_ruff(linter=True, formatter=False, remove=True)

                # Assert
                hook_names = get_hook_ids()

            # 1. File exists
            assert (uv_init_repo_dir / ".pre-commit-config.yaml").exists()

            # 2. Hook is in the file
            assert "ruff" not in hook_names
            assert "ruff-format" in hook_names

            # 3. Test file contents
            assert (uv_init_repo_dir / ".pre-commit-config.yaml").read_text() == (
                """\
repos:
  - repo: local
    hooks:
      - id: ruff-format
        name: ruff-format
        types_or:
          - python
          - pyi
          - jupyter
        always_run: true
        entry: uv run --frozen --offline ruff format --force-exclude
        language: system
        require_serial: true
"""
            )

    class TestBitbucketIntegration:
        def test_add_linter_only(self, tmp_path: Path):
            # Arrange
            (tmp_path / "bitbucket-pipelines.yml").write_text("""\
image: atlassian/default-image:3
""")

            # Act
            with change_cwd(tmp_path), files_manager():
                use_ruff(linter=True, formatter=False)

            # Assert
            assert (tmp_path / "bitbucket-pipelines.yml").exists()
            contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
            assert "ruff check" in contents
            assert "ruff format" not in contents

        def test_add_formatter_only(self, tmp_path: Path):
            # Arrange
            (tmp_path / "bitbucket-pipelines.yml").write_text("""\
image: atlassian/default-image:3
""")

            # Act
            with change_cwd(tmp_path), files_manager():
                use_ruff(linter=False, formatter=True)

            # Assert
            assert (tmp_path / "bitbucket-pipelines.yml").exists()
            contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
            assert "ruff check" not in contents
            assert "ruff format" in contents

        def test_remove_linter_only(self, uv_init_dir: Path):
            # Arrange
            (uv_init_dir / "bitbucket-pipelines.yml").write_text(
                """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Run Ruff
            script:
              - uv run ruff check --fix --force-exclude
"""
            )

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff(linter=True, formatter=False, remove=True)

            # Assert
            contents = (uv_init_dir / "bitbucket-pipelines.yml").read_text()
            assert (
                contents
                == """\
image: atlassian/default-image:3
definitions:
    caches:
        uv: ~/.cache/uv
    script_items:
      - &install-uv |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.local/bin/env
        export UV_LINK_MODE=copy
        uv --version
pipelines:
    default:
      - step:
            name: Placeholder - add your own steps!
            caches:
              - uv
            script:
              - *install-uv
              - echo 'Hello, world!'
"""
            )

        def test_remove_formatter_only_unchanged(self, uv_init_dir: Path):
            # Arrange
            (uv_init_dir / "bitbucket-pipelines.yml").write_text(
                """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Run Ruff
            script:
              - uv run ruff check --fix --force-exclude
"""
            )

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff(linter=False, formatter=True, remove=True)

            # Assert
            contents = (uv_init_dir / "bitbucket-pipelines.yml").read_text()
            assert (
                contents
                == """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Run Ruff
            script:
              - uv run ruff check --fix --force-exclude
"""
            )

    class TestConfig:
        def test_removed(self, uv_init_dir: Path):
            # Arrange
            (uv_init_dir / ".ruff.toml").write_text(
                """\
[lint]
select = ["A", "B", "C"]
"""
            )

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff(remove=True)

            # Assert
            assert not (uv_init_dir / ".ruff.toml").exists()

        def test_adding_to_file(self, uv_init_dir: Path):
            # Arrange
            (uv_init_dir / ".ruff.toml").touch()

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff()

            # Assert
            assert (uv_init_dir / ".ruff.toml").exists()
            assert "[lint]" in (uv_init_dir / ".ruff.toml").read_text()

        def test_highest_priority(self, uv_init_dir: Path):
            # Arrange
            (uv_init_dir / ".ruff.toml").touch()
            (uv_init_dir / "pyproject.toml").touch()
            (uv_init_dir / "ruff.toml").touch()

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff()

            # Assert
            assert "[lint]" in (uv_init_dir / ".ruff.toml").read_text()
            assert "[lint]" not in (uv_init_dir / "pyproject.toml").read_text()
            assert (uv_init_dir / "ruff.toml").read_text() == ""

        def test_removed_from_all_files(self, uv_init_dir: Path):
            # Arrange
            (uv_init_dir / ".ruff.toml").write_text(
                """\
[lint]
select = ["A", "B", "C"]
"""
            )
            (uv_init_dir / "pyproject.toml").write_text(
                """\
[tool.ruff.lint]
select = ["A", "B", "C"]
"""
            )
            (uv_init_dir / "ruff.toml").write_text(
                """\
[lint]
select = ["A", "B", "C"]
"""
            )

            # Act
            with change_cwd(uv_init_dir), files_manager():
                use_ruff(remove=True)

            # Assert
            assert not (uv_init_dir / ".ruff.toml").exists()
            assert (
                "[tool.ruff.lint]" not in (uv_init_dir / "pyproject.toml").read_text()
            )
            assert not (uv_init_dir / "ruff.toml").exists()


class TestUseTool:
    def test_add_all_tool(self, uv_init_dir: Path):
        # Act
        with change_cwd(uv_init_dir), files_manager():
            for tool in ALL_TOOLS:
                use_tool(tool)
