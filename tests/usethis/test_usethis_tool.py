from pathlib import Path

import pytest
import requests

from usethis._config import usethis_config
from usethis._console import box_print
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.pre_commit.hooks import _PLACEHOLDER_ID, get_hook_names
from usethis._integrations.pre_commit.schema import HookDefinition, LocalRepo, UriRepo
from usethis._integrations.uv.deps import Dependency, add_deps_to_group
from usethis._test import change_cwd
from usethis._tool import ConfigEntry, ConfigItem, ConfigSpec, PyprojectTOMLTool, Tool


class DefaultTool(Tool):
    """An example tool for testing purposes.

    This tool has minimal non-default configuration.
    """

    @property
    def name(self) -> str:
        return "default_tool"

    def print_how_to_use(self) -> None:
        box_print("How to use default_tool")


class MyTool(Tool):
    """An example tool for testing purposes.

    This tool has maximal non-default configuration.
    """

    @property
    def name(self) -> str:
        return "my_tool"

    def print_how_to_use(self) -> None:
        box_print("How to use my_tool")

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        deps = [
            Dependency(name=self.name),
            Dependency(name="black"),
            Dependency(name="flake8"),
        ]
        if unconditional:
            deps.append(Dependency(name="pytest"))
        return deps

    def get_pre_commit_repos(self) -> list[LocalRepo | UriRepo]:
        return [
            UriRepo(
                repo=f"repo for {self.name}",
                hooks=[HookDefinition(id="deptry")],
            )
        ]

    def get_config_spec(self) -> ConfigSpec:
        return ConfigSpec(
            file_manager_by_relative_path={
                Path("pyproject.toml"): PyprojectTOMLManager(),
            },
            resolution="first",
            config_items=[
                ConfigItem(
                    root={
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", self.name],
                            value={"key": "value"},
                        )
                    },
                    managed=True,
                )
            ],
        )

    def get_associated_ruff_rules(self) -> list[str]:
        return ["MYRULE"]

    def get_managed_files(self) -> list[Path]:
        return [Path("mytool-config.yaml")]

    def get_managed_pyproject_keys(self) -> list[list[str]]:
        return [["tool", self.name], ["project", "classifiers"]]


class TwoHooksTool(Tool):
    @property
    def name(self) -> str:
        return "two_hooks_tool"

    def print_how_to_use(self) -> None:
        box_print("How to use two_hooks_tool")

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
            assert tool.get_dev_deps() == []

        def test_specific(self):
            tool = MyTool()
            assert tool.get_dev_deps() == [
                Dependency(name="my_tool"),
                Dependency(name="black"),
                Dependency(name="flake8"),
            ]

    class TestPrintHowToUse:
        def test_default(self, capsys: pytest.CaptureFixture[str]):
            tool = DefaultTool()
            tool.print_how_to_use()
            captured = capsys.readouterr()
            assert captured.out == "☐ How to use default_tool\n"

        def test_specific(self, capsys: pytest.CaptureFixture[str]):
            tool = MyTool()
            tool.print_how_to_use()
            captured = capsys.readouterr()
            assert captured.out == "☐ How to use my_tool\n"

    class TestGetPreCommitRepoConfigs:
        def test_default(self):
            tool = DefaultTool()
            assert tool.get_pre_commit_repos() == []

        def test_specific(self):
            tool = MyTool()
            assert tool.get_pre_commit_repos() == [
                UriRepo(repo="repo for my_tool", hooks=[HookDefinition(id="deptry")])
            ]

    # TODO test get_config_spec

    class TestGetAssociatedRuffRules:
        def test_default(self):
            tool = DefaultTool()
            assert tool.get_associated_ruff_rules() == []

        def test_specific(self):
            tool = MyTool()
            assert tool.get_associated_ruff_rules() == ["MYRULE"]

    class TestGetManagedFiles:
        def test_default(self):
            tool = DefaultTool()
            assert tool.get_managed_files() == []

        def test_specific(self):
            tool = MyTool()
            assert tool.get_managed_files() == [
                Path("mytool-config.yaml"),
            ]

    class TestIsUsed:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_some_deps(self, uv_init_dir: Path):
            # Arrange
            tool = MyTool()
            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                add_deps_to_group(
                    [
                        Dependency(name="black"),
                    ],
                    "eggs",
                )

                # Act
                result = tool.is_used()

            # Assert
            assert result

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
            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                Path("mytool-config.yaml").mkdir()

                # Act
                result = tool.is_used()

            # Assert
            assert not result

        def test_pyproject(self, uv_init_dir: Path):
            # Arrange
            tool = MyTool()
            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                PyprojectTOMLManager().set_value(
                    keys=["tool", "my_tool", "key"], value="value"
                )

                # Act
                result = tool.is_used()

            # Assert
            assert result

        def test_empty(self, uv_init_dir: Path):
            # Arrange
            tool = MyTool()

            # Act
            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                result = tool.is_used()

            # Assert
            assert not result

        def test_dev_deps(self, uv_init_dir: Path):
            # Arrange
            tool = MyTool()

            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                add_deps_to_group(
                    [
                        Dependency(name="black"),
                    ],
                    "dev",
                )

                # Act
                result = tool.is_used()

            # Assert
            assert result

        def test_test_deps(self, uv_init_dir: Path):
            # Arrange
            tool = MyTool()

            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                add_deps_to_group(
                    [
                        Dependency(name="pytest"),
                    ],
                    "test",
                )

                # Act
                result = tool.is_used()

            # Assert
            assert result

        def test_not_extra_dev_deps(self, uv_init_dir: Path):
            # Arrange
            tool = MyTool()

            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                add_deps_to_group(
                    [
                        Dependency(name="isort"),
                    ],
                    "test",
                )

                # Act
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

                def print_how_to_use(self) -> None:
                    box_print("How to use no_repo_configs_tool")

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

                def print_how_to_use(self) -> None:
                    box_print("How to use multi_repo_tool")

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
                # `use_pre_commit` interface.
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
                out, err = capfd.readouterr()
                assert not err
                assert out == (
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
                out, err = capfd.readouterr()
                assert not err
                assert out == (
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

                def print_how_to_use(self) -> None:
                    box_print("How to use two_repo_tool")

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

    # TODO need to refactor these tests
    #     class TestAddPyprojectConfigs:
    #         def test_no_config(self, tmp_path: Path):
    #             # Arrange
    #             class NoConfigTool(Tool):
    #                 @property
    #                 def name(self) -> str:
    #                     return "no_config_tool"

    #                 def print_how_to_use(self) -> None:
    #                     box_print("How to use no_config_tool")

    #             nc_tool = NoConfigTool()

    #             # Act
    #             with change_cwd(tmp_path):
    #                 nc_tool.add_pyproject_configs()

    #                 # Assert
    #                 assert not (tmp_path / "pyproject.toml").exists()

    #         def test_empty(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
    #             # Arrange
    #             class ThisTool(Tool):
    #                 @property
    #                 def name(self) -> str:
    #                     return "mytool"

    #                 def print_how_to_use(self) -> None:
    #                     box_print("How to use this_tool")

    #                 def get_pyproject_configs(self) -> list[PyprojectConfig]:
    #                     return [
    #                         PyprojectConfig(
    #                             id_keys=["tool", "mytool"],
    #                             value={"key": "value"},
    #                         ),
    #                     ]

    #             (tmp_path / "pyproject.toml").write_text("")

    #             # Act
    #             with change_cwd(tmp_path), PyprojectTOMLManager():
    #                 ThisTool().add_pyproject_configs()

    #             # Assert
    #             assert (
    #                 (tmp_path / "pyproject.toml").read_text()
    #                 == """\
    # [tool.mytool]
    # key = "value"
    # """
    #             )
    #             out, err = capfd.readouterr()
    #             assert not err
    #             assert out == "✔ Adding mytool config to 'pyproject.toml'.\n"

    #         def test_differing_sections(
    #             self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
    #         ):
    #             # https://github.com/nathanjmcdougall/usethis-python/issues/184

    #             # Arrange
    #             class ThisTool(Tool):
    #                 @property
    #                 def name(self) -> str:
    #                     return "mytool"

    #                 def print_how_to_use(self) -> None:
    #                     box_print("How to use this_tool")

    #                 def get_pyproject_configs(self) -> list[PyprojectConfig]:
    #                     return [
    #                         PyprojectConfig(
    #                             id_keys=["tool", "mytool", "name"],
    #                             value="Modular Design",
    #                         ),
    #                         PyprojectConfig(
    #                             id_keys=["tool", "mytool", "root_packages"],
    #                             value=["example"],
    #                         ),
    #                     ]

    #             (tmp_path / "pyproject.toml").write_text(
    #                 """\
    # [tool.mytool]
    # name = "Modular Design"
    # """
    #             )

    #             # Act
    #             with change_cwd(tmp_path), PyprojectTOMLManager():
    #                 ThisTool().add_pyproject_configs()

    #             # Assert
    #             assert (
    #                 (tmp_path / "pyproject.toml").read_text()
    #                 == """\
    # [tool.mytool]
    # name = "Modular Design"
    # root_packages = ["example"]
    # """
    #             )
    #             out, err = capfd.readouterr()
    #             assert not err
    #             assert out == "✔ Adding mytool config to 'pyproject.toml'.\n"

    class TestRemoveManagedFiles:
        def test_no_files(self, tmp_path: Path):
            # Arrange
            tool = DefaultTool()

            # Act
            with change_cwd(tmp_path):
                tool.remove_managed_files()

                # Assert
                assert not (tmp_path / "mytool-config.yaml").exists()

        def test_file(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
            # Arrange
            tool = MyTool()
            (tmp_path / "mytool-config.yaml").write_text("")

            # Act
            with change_cwd(tmp_path):
                tool.remove_managed_files()

                # Assert
                assert not (tmp_path / "mytool-config.yaml").exists()

            out, err = capfd.readouterr()
            assert not err
            assert out == "✔ Removing 'mytool-config.yaml'.\n"

        def test_dir_not_removed(self, tmp_path: Path):
            # Arrange
            tool = MyTool()
            (tmp_path / "mytool-config.yaml").mkdir()

            # Act
            with change_cwd(tmp_path):
                tool.remove_managed_files()

                # Assert
                assert (tmp_path / "mytool-config.yaml").exists()


class TestDeptryTool:
    """Tests for DeptryTool."""

    # TODO need to refactor these tests
    # def test_get_pyproject_id_keys(self):
    #     """Test that get_pyproject_id_keys returns the correct keys."""
    #     # Arrange
    #     tool = DeptryTool()

    #     # Act
    #     result = tool.get_managed_pyproject_keys()

    #     # Assert
    #     assert result == [["tool", "deptry"]]


#     def test_remove_pyproject_configs_removes_deptry_section(self, tmp_path: Path):
#         """Test that remove_pyproject_configs removes the deptry section."""
#         # Arrange
#         pyproject = tmp_path / "pyproject.toml"
#         pyproject.write_text("""[tool.deptry]
# ignore_missing = ["pytest"]
# """)

#         # Act
#         with change_cwd(tmp_path), PyprojectTOMLManager():
#             tool = DeptryTool()
#             tool.remove_pyproject_configs()

#         # Assert
#         assert "[tool.deptry]" not in pyproject.read_text()
#         assert "ignore_missing" not in pyproject.read_text()

# TODO I'm not sure this test is coherent anymore. Try and understand this.
# def test_config_keys_are_subkeys_of_id_keys(self):
#     """Test that all config keys are subkeys of id keys."""
#     # Arrange
#     tool = DeptryTool()

#     # Act
#     id_keys = tool.get_managed_pyproject_keys()
#     configs = tool.get_pyproject_configs()

#     # Assert

#     for config in configs:
#         # For each config, check if its keys are a subset of any id_keys
#         assert any(config.id_keys[: len(id_key)] == id_key for id_key in id_keys), (
#             f"Config keys {config.id_keys} not covered by ID keys {id_keys}"
#         )

# TODO I'm not sure this test is coherent anymore. Try and understand this.
# @pytest.mark.parametrize("tool", ALL_TOOLS)
# def test_all_tools_config_keys_are_subkeys_of_id_keys(tool: Tool):
#     """Test that all tools' config keys are subkeys of their ID keys."""
#     id_keys = tool.get_managed_pyproject_keys()
#     configs = tool.get_pyproject_configs()

#     for config in configs:
#         # For each config, check if its keys are a subset of any id_keys
#         assert any(config.id_keys[: len(id_key)] == id_key for id_key in id_keys), (
#             f"Config keys {config.id_keys} not covered by ID keys in {tool.name}"
#         )


class TestPyprojectTOMLTool:
    class TestPrintHowToUse:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_link_isnt_dead(self):
            """A regression test."""

            # Arrange
            url = (
                "https://packaging.python.org/en/latest/guides/writing-pyproject-toml/"
            )

            if not usethis_config.offline:
                # Act
                result = requests.head(url)

                # Assert
                assert result.status_code == 200

        def test_some_output(self, capfd: pytest.CaptureFixture[str]):
            # Arrange
            tool = PyprojectTOMLTool()

            # Act
            tool.print_how_to_use()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out

    class TestName:
        def test_value(self):
            # Arrange
            tool = PyprojectTOMLTool()

            # Act
            result = tool.name

            # Assert
            assert result == "pyproject.toml"

    class TestDevDeps:
        def test_none(self):
            # Arrange
            tool = PyprojectTOMLTool()

            # Act
            result = tool.get_dev_deps()

            # Assert
            assert result == []
