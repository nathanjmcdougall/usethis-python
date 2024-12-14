from pathlib import Path

import pytest

from usethis._integrations.pre_commit.hooks import _PLACEHOLDER_ID, get_hook_names
from usethis._integrations.pre_commit.schema import HookDefinition, LocalRepo, UriRepo
from usethis._integrations.pyproject.config import PyProjectConfig
from usethis._integrations.pyproject.core import set_config_value
from usethis._integrations.uv.deps import add_deps_to_group
from usethis._test import change_cwd
from usethis._tool import Tool


class DefaultTool(Tool):
    """An example tool for testing purposes.

    This tool has minimal non-default configuration.
    """

    @property
    def name(self) -> str:
        return "default_tool"


class MyTool(Tool):
    """An example tool for testing purposes.

    This tool has maximal non-default configuration.
    """

    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def dev_deps(self) -> list[str]:
        return [self.name, "black", "flake8"]

    def get_pre_commit_repos(self) -> list[LocalRepo | UriRepo]:
        return [
            UriRepo(
                repo=f"repo for {self.name}",
                hooks=[HookDefinition(id="deptry")],
            )
        ]

    def get_pyproject_configs(self) -> list[PyProjectConfig]:
        return [
            PyProjectConfig(id_keys=["tool", self.name], main_contents={"key": "value"})
        ]

    def get_associated_ruff_rules(self) -> list[str]:
        return ["MYRULE"]

    def get_unique_dev_deps(self) -> list[str]:
        return [self.name, "isort"]  # Obviously "isort" is not mytool's! For testing.

    def get_managed_files(self) -> list[Path]:
        return [Path("mytool-config.yaml")]

    def get_pyproject_id_keys(self) -> list[list[str]]:
        return [["tool", self.name], ["project", "classifiers"]]


class TwoHooksTool(Tool):
    @property
    def name(self) -> str:
        return "two_hooks_tool"

    def get_pre_commit_repos(self) -> list[LocalRepo | UriRepo]:
        return [
            UriRepo(
                repo="example",
                hooks=[
                    HookDefinition(id="ruff"),
                    HookDefinition(id="ruff-format"),
                ],
            ),
        ]


class TestTool:
    class TestName:
        def test_default(self):
            tool = DefaultTool()
            assert tool.name == "default_tool"

        def test_specific(self):
            tool = MyTool()
            assert tool.name == "my_tool"

    class TestDevDeps:
        def test_default(self):
            tool = DefaultTool()
            assert tool.dev_deps == []

        def test_specific(self):
            tool = MyTool()
            assert tool.dev_deps == ["my_tool", "black", "flake8"]

    class TestGetPreCommitRepoConfigs:
        def test_default(self):
            tool = DefaultTool()
            assert tool.get_pre_commit_repos() == []

        def test_specific(self):
            tool = MyTool()
            assert tool.get_pre_commit_repos() == [
                UriRepo(repo="repo for my_tool", hooks=[HookDefinition(id="deptry")])
            ]

    class TestGetPyprojectConfigs:
        def test_default(self):
            tool = DefaultTool()
            assert tool.get_pyproject_configs() == []

        def test_specific(self):
            tool = MyTool()
            assert tool.get_pyproject_configs() == [
                PyProjectConfig(
                    id_keys=["tool", "my_tool"], main_contents={"key": "value"}
                )
            ]

    class TestGetAssociatedRuffRules:
        def test_default(self):
            tool = DefaultTool()
            assert tool.get_associated_ruff_rules() == []

        def test_specific(self):
            tool = MyTool()
            assert tool.get_associated_ruff_rules() == ["MYRULE"]

    class TestGetUniqueDevDeps:
        def test_default(self):
            tool = DefaultTool()
            assert tool.get_unique_dev_deps() == []

        def test_specific(self):
            tool = MyTool()
            assert tool.get_unique_dev_deps() == ["my_tool", "isort"]

    class TestGetManagedFiles:
        def test_default(self):
            tool = DefaultTool()
            assert tool.get_managed_files() == []

        def test_specific(self):
            tool = MyTool()
            assert tool.get_managed_files() == [
                Path("mytool-config.yaml"),
            ]

    class TestGetPyprojectIdKeys:
        def test_default(self):
            tool = DefaultTool()
            assert tool.get_pyproject_id_keys() == []

        def test_specific(self):
            tool = MyTool()
            assert tool.get_pyproject_id_keys() == [
                ["tool", "my_tool"],
                ["project", "classifiers"],
            ]

    class TestIsUsed:
        def test_some_deps(self, uv_init_dir: Path, vary_network_conn: None):
            # Arrange
            tool = MyTool()
            with change_cwd(uv_init_dir):
                add_deps_to_group(["isort"], "eggs")

                # Act
                result = tool.is_used()

            # Assert
            assert result

        def test_non_managed_deps(self, uv_init_dir: Path, vary_network_conn: None):
            # Arrange
            tool = MyTool()
            with change_cwd(uv_init_dir):
                add_deps_to_group(["black"], "eggs")
                # Act
                result = tool.is_used()

            # Assert
            assert not result

        def test_files(self, uv_init_dir: Path):
            # Arrange
            tool = MyTool()
            with change_cwd(uv_init_dir):
                Path("mytool-config.yaml").touch()

                # Act
                result = tool.is_used()

            # Assert
            assert result

        def test_dir(self, uv_init_dir: Path):
            # Arrange
            tool = MyTool()
            with change_cwd(uv_init_dir):
                Path("mytool-config.yaml").mkdir()

                # Act
                result = tool.is_used()

            # Assert
            assert not result

        def test_pyproject(self, uv_init_dir: Path):
            # Arrange
            tool = MyTool()
            with change_cwd(uv_init_dir):
                set_config_value(["tool", "my_tool", "key"], "value")

                # Act
                result = tool.is_used()

            # Assert
            assert result

        def test_empty(self, uv_init_dir: Path):
            # Arrange
            tool = MyTool()

            # Act
            with change_cwd(uv_init_dir):
                result = tool.is_used()

            # Assert
            assert not result

    class TestAddPreCommitRepoConfigs:
        def test_no_repo_configs(self, uv_init_dir: Path):
            # Arrange
            class NoRepoConfigsTool(Tool):
                @property
                def name(self) -> str:
                    return "no_repo_configs_tool"

                def get_pre_commit_repos(self) -> list[LocalRepo | UriRepo]:
                    return []

            nrc_tool = NoRepoConfigsTool()

            # Act
            with change_cwd(uv_init_dir):
                nrc_tool.add_pre_commit_repo_configs()

                # Assert
                assert not (uv_init_dir / ".pre-commit-config.yaml").exists()

        def test_multiple_repo_configs(self, uv_init_dir: Path):
            # Arrange
            class MultiRepoTool(Tool):
                @property
                def name(self) -> str:
                    return "multi_repo_tool"

                def get_pre_commit_repos(self) -> list[LocalRepo | UriRepo]:
                    return [
                        UriRepo(
                            repo="example",
                            hooks=[
                                HookDefinition(id="ruff"),
                                HookDefinition(id="ruff-format"),
                            ],
                        ),
                        UriRepo(
                            repo="other",
                            hooks=[
                                HookDefinition(
                                    id="deptry",
                                )
                            ],
                        ),
                    ]

            mrt_tool = MultiRepoTool()

            # Act
            with change_cwd(uv_init_dir):
                # Currently this feature isn't implemented, so when it is this
                # with-raises block can be removed and the test no longer needs to be
                # skipped.
                with pytest.raises(NotImplementedError):
                    mrt_tool.add_pre_commit_repo_configs()
                pytest.skip("Multiple hooks in one repo not supported yet.")

                # Assert
                assert (uv_init_dir / ".pre-commit-config.yaml").exists()

                # Note that this deliberately doesn't include validate-pyproject
                # That should only be included as a default when using the
                # `use_precommit` interface.
                assert get_hook_names() == ["ruff", "ruff-format", "deptry"]

        def test_file_created(self, tmp_path: Path):
            # Arrange
            tool = MyTool()

            # Act
            with change_cwd(tmp_path):
                tool.add_pre_commit_repo_configs()

                # Assert
                assert (tmp_path / ".pre-commit-config.yaml").exists()

        def test_file_not_created(self, tmp_path: Path):
            # Arrange
            tool = DefaultTool()

            # Act
            with change_cwd(tmp_path):
                tool.add_pre_commit_repo_configs()

                # Assert
                assert not (tmp_path / ".pre-commit-config.yaml").exists()

        def test_add_successful(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            tool = MyTool()

            # Act
            with change_cwd(tmp_path):
                tool.add_pre_commit_repo_configs()

                # Assert
                output = capfd.readouterr().out
                assert output == (
                    "✔ Writing '.pre-commit-config.yaml'.\n"
                    "✔ Adding hook 'deptry' to '.pre-commit-config.yaml'.\n"
                )
                assert "deptry" in get_hook_names()

        def test_add_two_hooks_in_one_repo_when_one_already_exists(
            self,
            tmp_path: Path,
            capfd: pytest.CaptureFixture[str],
        ):
            # Arrange
            th_tool = TwoHooksTool()

            # Create a pre-commit config file with one of the two hooks
            (tmp_path / ".pre-commit-config.yaml").write_text("""\
repos:
  - repo: local
    hooks:
      - id: ruff
        entry: echo "different now!"
""")

            # Act
            with change_cwd(tmp_path):
                # Currently, we are expecting multiple hooks to not be supported.
                # At the point where we do support it, this with-raises block and
                # test skip can be removed - the rest of the test becomes valid.
                with pytest.raises(NotImplementedError):
                    th_tool.add_pre_commit_repo_configs()
                pytest.skip("Multiple hooks in one repo not supported yet")

                # Assert
                output = capfd.readouterr().out
                assert output == (
                    "✔ Adding hook 'ruff-format' to '.pre-commit-config.yaml'.\n"
                )
                assert get_hook_names() == ["ruff", "ruff-format"]

            assert (
                (tmp_path / ".pre-commit-config.yaml").read_text()
                == """\
repos:
  - repo: local
    hooks:
      - id: ruff-format
        entry: ruff format
      - id: ruff
        entry: echo "different now!"
"""
            )

        def test_two_hooks_one_repo(
            self,
            tmp_path: Path,
            capfd: pytest.CaptureFixture[str],
        ):
            # Arrange
            th_tool = TwoHooksTool()

            # Act
            with change_cwd(tmp_path):
                # Currently, multiple hooks are not supported.
                # If we do ever support it, this with-raises block and
                # test skip can be removed. Instead, we will need to write this test.
                with pytest.raises(NotImplementedError):
                    th_tool.add_pre_commit_repo_configs()
                pytest.skip("Multiple hooks in one repo not supported yet")

    class TestRemovePreCommitRepoConfigs:
        def test_no_file_remove_none(self, tmp_path: Path):
            # Arrange
            nc_tool = DefaultTool()

            # Act
            with change_cwd(tmp_path):
                nc_tool.remove_pre_commit_repo_configs()

                # Assert
                assert not (tmp_path / ".pre-commit-config.yaml").exists()

        def test_no_file_remove_one(self, tmp_path: Path):
            # Arrange
            tool = MyTool()

            # Act
            with change_cwd(tmp_path):
                tool.remove_pre_commit_repo_configs()

                # Assert
                assert not (tmp_path / ".pre-commit-config.yaml").exists()

        def test_one_hook_remove_none(self, tmp_path: Path):
            # Arrange
            tool = DefaultTool()

            # Create a pre-commit config file with one hook
            contents = """\
repos:
  - repo: local
    hooks:
      - id: ruff-format
        entry: ruff format
"""
            (tmp_path / ".pre-commit-config.yaml").write_text(contents)

            # Act
            with change_cwd(tmp_path):
                tool.remove_pre_commit_repo_configs()

                # Assert
                assert (tmp_path / ".pre-commit-config.yaml").exists()
                assert get_hook_names() == ["ruff-format"]
                assert (tmp_path / ".pre-commit-config.yaml").read_text() == contents

        def test_one_hook_remove_different_one(self, tmp_path: Path):
            # Arrange
            tool = MyTool()

            # Create a pre-commit config file with one hook
            contents = """\
repos:
  - repo: local
    hooks:
      - id: ruff-format
        entry: ruff format
"""
            (tmp_path / ".pre-commit-config.yaml").write_text(contents)

            # Act
            with change_cwd(tmp_path):
                tool.remove_pre_commit_repo_configs()

                # Assert
                assert (tmp_path / ".pre-commit-config.yaml").exists()
                assert get_hook_names() == ["ruff-format"]
                assert (tmp_path / ".pre-commit-config.yaml").read_text() == contents

        def test_one_hook_remove_same_hook(self, tmp_path: Path):
            # Arrange
            tool = MyTool()

            # Create a pre-commit config file with one hook
            contents = """\
repos:
  - repo: local
    hooks:
      - id: deptry
        entry: deptry
"""
            (tmp_path / ".pre-commit-config.yaml").write_text(contents)

            # Act
            with change_cwd(tmp_path):
                tool.remove_pre_commit_repo_configs()

                # Assert
                assert (tmp_path / ".pre-commit-config.yaml").exists()
                assert get_hook_names() == [_PLACEHOLDER_ID]

        def test_two_repos_remove_same_two(self, tmp_path: Path):
            # Arrange
            class TwoRepoTool(Tool):
                @property
                def name(self) -> str:
                    return "two_repo_tool"

                def get_pre_commit_repos(self) -> list[LocalRepo | UriRepo]:
                    return [
                        UriRepo(
                            repo="example",
                            hooks=[
                                HookDefinition(id="ruff"),
                                HookDefinition(id="ruff-format"),
                            ],
                        ),
                        UriRepo(
                            repo="other",
                            hooks=[
                                HookDefinition(
                                    id="deptry",
                                )
                            ],
                        ),
                    ]

            tr_tool = TwoRepoTool()

            # Create a pre-commit config file with two hooks
            contents = """\
repos:
    - repo: local
      hooks:
        - id: ruff-format
          entry: ruff format
        - id: ruff
          entry: ruff check
"""

            (tmp_path / ".pre-commit-config.yaml").write_text(contents)

            # Act
            with change_cwd(tmp_path):
                tr_tool.remove_pre_commit_repo_configs()

                # Assert
                assert (tmp_path / ".pre-commit-config.yaml").exists()
                assert get_hook_names() == [_PLACEHOLDER_ID]
