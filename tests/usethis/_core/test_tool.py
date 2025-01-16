import subprocess
from pathlib import Path

import pytest

from usethis._config import usethis_config
from usethis._core.ci import use_ci_bitbucket
from usethis._core.tool import (
    use_deptry,
    use_pre_commit,
    use_pyproject_fmt,
    use_pytest,
    use_requirements_txt,
    use_ruff,
)
from usethis._integrations.pre_commit.hooks import (
    _HOOK_ORDER,
    get_hook_names,
)
from usethis._integrations.uv.call import call_uv_subprocess
from usethis._integrations.uv.deps import (
    add_deps_to_group,
    get_deps_from_group,
)
from usethis._test import change_cwd
from usethis._tool import ALL_TOOLS


class TestAllHooksList:
    def test_subset_hook_names(self):
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


class TestDeptry:
    class TestAdd:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_dependency_added(self, uv_init_dir: Path):
            # Act
            with change_cwd(uv_init_dir):
                use_deptry()

                # Assert
                (dev_dep,) = get_deps_from_group("dev")
            assert dev_dep == "deptry"

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_stdout(
            self,
            uv_init_dir: Path,
            capfd: pytest.CaptureFixture[str],
        ):
            # Act
            with change_cwd(uv_init_dir):
                use_deptry()

            # Assert
            out, _ = capfd.readouterr()
            assert out == (
                "✔ Adding dependency 'deptry' to the 'dev' group in 'pyproject.toml'.\n"
                "☐ Run 'deptry src' to run deptry.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_run_deptry_fail(self, uv_init_dir: Path):
            # Arrange
            f = uv_init_dir / "bad.py"
            f.write_text("import broken_dependency")

            # Act
            with change_cwd(uv_init_dir):
                use_deptry()

            # Assert
            with pytest.raises(subprocess.CalledProcessError):
                subprocess.run(["deptry", "."], cwd=uv_init_dir, check=True)

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_run_deptry_pass(self, uv_init_dir: Path):
            # Arrange
            f = uv_init_dir / "good.py"
            f.write_text("import sys")

            # Act
            with change_cwd(uv_init_dir):
                use_deptry()

            # Assert
            subprocess.run(["deptry", "."], cwd=uv_init_dir, check=True)

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_pre_commit_after(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(uv_init_repo_dir):
                use_deptry()
                use_pre_commit()

                # Assert
                hook_names = get_hook_names()

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
        entry: uv run --frozen deptry src
        language: system
        pass_filenames: false
"""
            )

            # 4. Check messages
            out, _ = capfd.readouterr()
            assert (
                out
                == (
                    "✔ Adding dependency 'deptry' to the 'dev' group in 'pyproject.toml'.\n"
                    "☐ Run 'deptry src' to run deptry.\n"
                    "✔ Adding dependency 'pre-commit' to the 'dev' group in 'pyproject.toml'.\n"
                    "✔ Writing '.pre-commit-config.yaml'.\n"
                    "✔ Adding hook 'deptry' to '.pre-commit-config.yaml'.\n"
                    "✔ Ensuring pre-commit is installed to Git.\n"
                    "✔ Ensuring pre-commit hooks are installed.\n"
                    "ℹ This may take a minute or so while the hooks are downloaded.\r"  # noqa: RUF001
                    "☐ Run 'pre-commit run --all-files' to run the hooks manually.\n"
                )
            )

    class TestRemove:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_dep(self, uv_init_dir: Path):
            with change_cwd(uv_init_dir):
                # Arrange
                add_deps_to_group(["deptry"], "dev")

                # Act
                use_deptry(remove=True)

                # Assert
                assert not get_deps_from_group("dev")

    class TestPreCommitIntegration:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_pre_commit_first(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            """Basically this checks that the placeholders gets removed."""
            with change_cwd(uv_init_repo_dir):
                # Arrange
                use_pre_commit()
                capfd.readouterr()

                # Act
                use_deptry()

                # Assert
                hook_names = get_hook_names()

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
        entry: uv run --frozen deptry src
        language: system
        pass_filenames: false
"""
            )

            # 4. Check messages
            out, _ = capfd.readouterr()
            assert out == (
                "✔ Adding dependency 'deptry' to the 'dev' group in 'pyproject.toml'.\n"
                "✔ Adding hook 'deptry' to '.pre-commit-config.yaml'.\n"
                "☐ Run 'deptry src' to run deptry.\n"
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
            with change_cwd(uv_init_repo_dir):
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
                "✔ Adding hook 'deptry' to '.pre-commit-config.yaml'.\n"
                "☐ Run 'deptry src' to run deptry.\n"
            )

        def test_remove(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            with change_cwd(uv_init_repo_dir), usethis_config.set(quiet=True):
                use_deptry()
                use_pre_commit()
                content = (uv_init_repo_dir / ".pre-commit-config.yaml").read_text()
                assert "deptry" in content

            # Act
            with change_cwd(uv_init_repo_dir):
                use_deptry(remove=True)

            # Assert
            content = (uv_init_repo_dir / ".pre-commit-config.yaml").read_text()
            assert "deptry" not in content


class TestPreCommit:
    class TestUse:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_fresh(self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]):
            # Act
            with change_cwd(uv_init_repo_dir):
                use_pre_commit()

                # Assert
                # Has dev dep
                (dev_dep,) = get_deps_from_group("dev")
                assert dev_dep == "pre-commit"
            # Correct stdout
            out, _ = capfd.readouterr()
            assert (
                out
                == (
                    "✔ Adding dependency 'pre-commit' to the 'dev' group in 'pyproject.toml'.\n"
                    "✔ Writing '.pre-commit-config.yaml'.\n"
                    "✔ Adding placeholder hook to '.pre-commit-config.yaml'.\n"
                    "☐ Remove the placeholder hook in '.pre-commit-config.yaml'.\n"
                    "☐ Replace it with your own hooks.\n"
                    "☐ Alternatively, use 'usethis tool' to add other tools and their hooks.\n"
                    "✔ Ensuring pre-commit is installed to Git.\n"
                    "✔ Ensuring pre-commit hooks are installed.\n"
                    "ℹ This may take a minute or so while the hooks are downloaded.\r"  # noqa: RUF001
                    "☐ Run 'pre-commit run --all-files' to run the hooks manually.\n"
                )
            )
            # Config file
            assert (uv_init_repo_dir / ".pre-commit-config.yaml").exists()
            contents = (uv_init_repo_dir / ".pre-commit-config.yaml").read_text()
            assert contents == (
                """\
repos:
  - repo: local
    hooks:
      - id: placeholder
        name: Placeholder - add your own hooks!
        entry: uv run python -c "print('hello world!')"
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
        entry: uv run python -c "print('hello world!')"
        language: system
"""
            )

            # Act
            with change_cwd(uv_init_repo_dir):
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
        entry: uv run python -c "print('hello world!')"
        language: system
"""
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_bad_commit(self, uv_init_repo_dir: Path):
            # Act
            with change_cwd(uv_init_repo_dir):
                use_pre_commit()
            subprocess.run(["git", "add", "."], cwd=uv_init_repo_dir, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Good commit"], cwd=uv_init_repo_dir, check=True
            )

            # Assert
            (uv_init_repo_dir / "pyproject.toml").write_text("[")
            subprocess.run(["git", "add", "."], cwd=uv_init_repo_dir, check=True)
            with pytest.raises(subprocess.CalledProcessError):
                subprocess.run(
                    ["git", "commit", "-m", "Bad commit"],
                    cwd=uv_init_repo_dir,
                    check=True,
                )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_requirements_txt_used(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir):
                # Arrange
                use_requirements_txt()

                # Act
                use_pre_commit()

            # Assert
            assert "uv-export" in get_hook_names()

    class TestRemove:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_config_file(self, uv_init_repo_dir: Path):
            # Arrange
            (uv_init_repo_dir / ".pre-commit-config.yaml").touch()

            # Act
            with change_cwd(uv_init_repo_dir):
                use_pre_commit(remove=True)

            # Assert
            assert not (uv_init_repo_dir / ".pre-commit-config.yaml").exists()

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_dep(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir):
                # Arrange
                add_deps_to_group(["pre-commit"], "dev")

                # Act
                use_pre_commit(remove=True)

                # Assert
                assert not get_deps_from_group("dev")

        def test_stdout(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            (uv_init_repo_dir / ".pre-commit-config.yaml").write_text(
                """\
repos:
  - repo: local
    hooks:
      - id: pre-commit
"""
            )

            # Act
            with change_cwd(uv_init_repo_dir):
                use_pre_commit(remove=True)

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Adding dependency 'pre-commit' to the 'dev' group in 'pyproject.toml'.\n"
                "✔ Ensuring pre-commit hooks are uninstalled.\n"
                "✔ Removing '.pre-commit-config.yaml'.\n"
                "✔ Removing dependency 'pre-commit' from the 'dev' group in 'pyproject.toml'.\n"
            )

        def test_requirements_txt_used(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_repo_dir):
                # Arrange
                with usethis_config.set(quiet=True):
                    use_pre_commit()
                    use_requirements_txt()

                # Act
                use_pre_commit(remove=True)

            # Assert
            out, _ = capfd.readouterr()
            assert out == (
                "✔ Ensuring pre-commit hooks are uninstalled.\n"
                "✔ Removing '.pre-commit-config.yaml'.\n"
                "✔ Removing dependency 'pre-commit' from the 'dev' group in 'pyproject.toml'.\n"
                "☐ Run 'uv export --no-dev --output-file=requirements.txt' to write \n'requirements.txt'.\n"
            )

    class TestBitbucketCIIntegration:
        def test_prexisting(self, uv_init_repo_dir: Path):
            # Arrange
            (uv_init_repo_dir / "bitbucket-pipelines.yml").write_text(
                """\
image: atlassian/default-image:3
"""
            )

            with change_cwd(uv_init_repo_dir):
                # Act
                use_pre_commit()

            # Assert
            contents = (uv_init_repo_dir / "bitbucket-pipelines.yml").read_text()
            assert "pre-commit" in contents

        def test_remove(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            with change_cwd(uv_init_repo_dir), usethis_config.set(quiet=True):
                use_pre_commit()
            (uv_init_repo_dir / "bitbucket-pipelines.yml").write_text(
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
            with change_cwd(uv_init_repo_dir):
                use_pre_commit(remove=True)

            # Assert
            contents = (uv_init_repo_dir / "bitbucket-pipelines.yml").read_text()
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
                "✔ Ensuring pre-commit hooks are uninstalled.\n"
                "✔ Removing '.pre-commit-config.yaml'.\n"
                "✔ Removing dependency 'pre-commit' from the 'dev' group in 'pyproject.toml'.\n"
            )


class TestPyprojectFmt:
    class TestAdd:
        class TestPyproject:
            @pytest.mark.usefixtures("_vary_network_conn")
            def test_added(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
                # Arrange
                with change_cwd(uv_init_dir), usethis_config.set(quiet=True):
                    add_deps_to_group(["pyproject-fmt"], "dev")
                content = (uv_init_dir / "pyproject.toml").read_text()

                # Act
                with change_cwd(uv_init_dir):
                    use_pyproject_fmt()

                # Assert
                assert (
                    uv_init_dir / "pyproject.toml"
                ).read_text() == content + "\n" + (
                    """\
[tool.pyproject-fmt]
keep_full_version = true
"""
                )
                out, _ = capfd.readouterr()
                assert out == (
                    "✔ Adding pyproject-fmt config to 'pyproject.toml'.\n"
                    "☐ Run 'pyproject-fmt pyproject.toml' to run pyproject-fmt.\n"
                )

        class TestDeps:
            @pytest.mark.usefixtures("_vary_network_conn")
            def test_added(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
                with change_cwd(uv_init_dir):
                    # Act
                    use_pyproject_fmt()

                    # Assert
                    assert get_deps_from_group("dev") == ["pyproject-fmt"]
                out, _ = capfd.readouterr()
                assert out == (
                    "✔ Adding dependency 'pyproject-fmt' to the 'dev' group in 'pyproject.toml'.\n"
                    "✔ Adding pyproject-fmt config to 'pyproject.toml'.\n"
                    "☐ Run 'pyproject-fmt pyproject.toml' to run pyproject-fmt.\n"
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
            with change_cwd(uv_init_dir):
                use_pyproject_fmt(remove=True)

            # Assert
            assert (uv_init_dir / "pyproject.toml").read_text() == ""

    class TestPreCommitIntegration:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_use_first(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir):
                # Arrange
                use_pre_commit()

                # Act
                use_pyproject_fmt()

                # Assert
                hook_names = get_hook_names()

            assert (uv_init_repo_dir / ".pre-commit-config.yaml").exists()
            assert "pyproject-fmt" in hook_names

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_use_after(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir):
                # Arrange
                use_pyproject_fmt()

                # Act
                use_pre_commit()

                # Assert
                hook_names = get_hook_names()

            assert (uv_init_repo_dir / ".pre-commit-config.yaml").exists()
            assert "pyproject-fmt" in hook_names

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_remove_with_precommit(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_repo_dir):
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
            with change_cwd(uv_init_repo_dir):
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


class TestPytest:
    class TestAdd:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_dep(self, uv_init_dir: Path):
            with change_cwd(uv_init_dir):
                use_pytest()

                assert {
                    "pytest",
                    "pytest-cov",
                    "coverage",
                } <= set(get_deps_from_group("test"))

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_bitbucket_integration(self, uv_init_dir: Path):
            with change_cwd(uv_init_dir):
                # Arrange
                use_ci_bitbucket()

                # Act
                use_pytest()

            # Assert
            assert "pytest" in (uv_init_dir / "bitbucket-pipelines.yml").read_text()

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
                with change_cwd(uv_init_dir):
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
                with change_cwd(uv_init_dir):
                    use_pytest(remove=True)

                # Assert
                out, _ = capfd.readouterr()
                assert out == ("✔ Disabling Ruff rule 'PT' in 'pyproject.toml'.\n")

        class TestPyproject:
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
                with change_cwd(uv_init_dir):
                    use_pytest(remove=True)

                # Assert
                assert (uv_init_dir / "pyproject.toml").read_text() == ""
                out, _ = capfd.readouterr()
                # N.B. we don't put `pytest` in quotes because we are referring to the
                # tool, not the package.
                assert out == "✔ Removing pytest config from 'pyproject.toml'.\n"

        class TestDependencies:
            def test_removed(self, uv_init_dir: Path):
                with change_cwd(uv_init_dir):
                    # Arrange
                    add_deps_to_group(["pytest"], "test")

                    # Act
                    use_pytest(remove=True)

                    # Assert
                    assert not get_deps_from_group("test")

        class TestBitbucketIntegration:
            def test_remove(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
                # Arrange
                with change_cwd(uv_init_dir), usethis_config.set(quiet=True):
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
                with change_cwd(uv_init_dir):
                    use_pytest(remove=True)

                # Assert
                out, err = capfd.readouterr()
                assert not err
                assert out.replace("\n", "").replace(" ", "") == (
                    "✔ Removing 'Test on 3.12' from default pipeline in 'bitbucket-pipelines.yml'.\n"
                    "✔ Adding cache 'uv' definition to 'bitbucket-pipelines.yml'.\n"
                    "✔ Removing pytest config from 'pyproject.toml'.\n"
                    "✔ Removing dependencies 'pytest', 'pytest-cov', 'coverage' from the 'test' group in 'pyproject.toml'.\n"
                    "✔ Removing '/tests'.\n"
                ).replace("\n", "").replace(" ", "")
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


class TestRuff:
    class TestAdd:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_dependency_added(self, uv_init_dir: Path):
            # Act
            with change_cwd(uv_init_dir):
                use_ruff()

                # Assert
                (dev_dep,) = get_deps_from_group("dev")
            assert dev_dep == "ruff"

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_stdout(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
            # Act
            with change_cwd(uv_init_dir):
                use_ruff()

            # Assert
            out, _ = capfd.readouterr()
            assert out == (
                "✔ Adding dependency 'ruff' to the 'dev' group in 'pyproject.toml'.\n"
                "✔ Adding Ruff config to 'pyproject.toml'.\n"
                "✔ Enabling Ruff rules 'A', 'C4', 'E4', 'E7', 'E9', 'EM', 'F', 'FURB', 'I', \n'PLE', 'PLR', 'RUF', 'SIM', 'UP' in 'pyproject.toml'.\n"
                "✔ Ignoring Ruff rules 'PLR2004', 'SIM108' in 'pyproject.toml'.\n"
                "☐ Run 'ruff check --fix' to run the Ruff linter with autofixes.\n"
                "☐ Run 'ruff format' to run the Ruff formatter.\n"
            )

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_pre_commit_first(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(uv_init_repo_dir):
                use_ruff()
                use_pre_commit()

                # Assert
                hook_names = get_hook_names()

            assert "ruff-format" in hook_names
            assert "ruff" in hook_names

        def test_creates_pyproject_toml(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(tmp_path):
                use_ruff()

            # Assert
            assert (tmp_path / "pyproject.toml").exists()
            out, err = capfd.readouterr()
            assert not err
            assert out.startswith("✔ Writing 'pyproject.toml'.\n")

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
            with change_cwd(uv_init_dir):
                use_ruff(remove=True)

            # Assert
            assert (uv_init_dir / "pyproject.toml").read_text() == ""

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_blank_slate(self, uv_init_dir: Path):
            # Arrange
            contents = (uv_init_dir / "pyproject.toml").read_text()

            # Act
            with change_cwd(uv_init_dir):
                use_ruff(remove=True)

            # Assert
            assert (uv_init_dir / "pyproject.toml").read_text() == contents

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_roundtrip(self, uv_init_dir: Path):
            # Arrange
            contents = (uv_init_dir / "pyproject.toml").read_text()

            # Act
            with change_cwd(uv_init_dir):
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

    class TestPrecommitIntegration:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_use_first(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir):
                # Arrange
                use_ruff()

                # Act
                use_pre_commit()

                # Assert
                hook_names = get_hook_names()

            assert "ruff-format" in hook_names
            assert "ruff" in hook_names

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_use_after(self, uv_init_repo_dir: Path):
            with change_cwd(uv_init_repo_dir):
                # Arrange
                use_pre_commit()

                # Act
                use_ruff()

                # Assert
                hook_names = get_hook_names()

            assert "ruff-format" in hook_names
            assert "ruff" in hook_names

        @pytest.mark.usefixtures("_vary_network_conn")
        def test_remove(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_repo_dir):
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
                "✔ Removing hook 'ruff-format' from '.pre-commit-config.yaml'.\n"
                "✔ Removing hook 'ruff' from '.pre-commit-config.yaml'.\n"
                "✔ Removing Ruff config from 'pyproject.toml'.\n"
                "✔ Removing dependency 'ruff' from the 'dev' group in 'pyproject.toml'.\n"
            )


class TestRequirementsTxt:
    class TestAdd:
        def test_start_from_nothing(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(tmp_path):
                use_requirements_txt()

            # Assert
            assert (tmp_path / "requirements.txt").exists()
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Writing 'pyproject.toml'.\n"
                "✔ Writing 'uv.lock'.\n"
                "✔ Writing 'requirements.txt'.\n"
                "☐ Run 'uv export --no-dev --output-file=requirements.txt' to write \n'requirements.txt'.\n"
            )

        def test_start_from_uv_init(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(uv_init_dir):
                use_requirements_txt()

            # Assert
            assert (uv_init_dir / "requirements.txt").exists()
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Writing 'uv.lock'.\n"
                "✔ Writing 'requirements.txt'.\n"
                "☐ Run 'uv export --no-dev --output-file=requirements.txt' to write \n'requirements.txt'.\n"
            )

        def test_start_from_uv_locked(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_dir):
                # Arrange
                call_uv_subprocess(["lock"])

                # Act
                use_requirements_txt()

            # Assert
            assert (uv_init_dir / "requirements.txt").exists()
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Writing 'requirements.txt'.\n"
                "☐ Run 'uv export --no-dev --output-file=requirements.txt' to write \n'requirements.txt'.\n"
            )

        def test_pre_commit(
            self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            with change_cwd(uv_init_repo_dir):
                # Arrange
                with usethis_config.set(quiet=True):
                    use_pre_commit()

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
        entry: uv export --frozen --no-dev --output-file=requirements.txt --quiet
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
                "☐ Run the 'pre-commit run uv-export' to write 'requirements.txt'.\n"
            )

    class TestRemove:
        def test_file_gone(self, tmp_path: Path):
            # Arrange
            (tmp_path / "requirements.txt").touch()

            # Act
            with change_cwd(tmp_path):
                use_requirements_txt(remove=True)

            # Assert
            assert not (tmp_path / "requirements.txt").exists()

        def test_requirements_dir(self, tmp_path: Path):
            # Arrange
            (tmp_path / "requirements.txt").mkdir()

            # Act
            with change_cwd(tmp_path):
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
            with change_cwd(tmp_path):
                use_requirements_txt(remove=True)

            # Assert
            assert (tmp_path / ".pre-commit-config.yaml").exists()
            content = (tmp_path / ".pre-commit-config.yaml").read_text()
            assert "uv-export" not in content

        def test_roundtrip(self, tmp_path: Path):
            with change_cwd(tmp_path):
                # Arrange
                use_requirements_txt()

                # Act
                use_requirements_txt(remove=True)

            # Assert
            assert not (tmp_path / "requirements.txt").exists()
