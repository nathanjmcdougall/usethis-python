from pathlib import Path

import pytest
import requests

from usethis._config import usethis_config
from usethis._config_file import DotRuffTOMLManager, RuffTOMLManager, files_manager
from usethis._console import box_print
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.pre_commit.hooks import _PLACEHOLDER_ID, get_hook_ids
from usethis._integrations.pre_commit.schema import HookDefinition, LocalRepo, UriRepo
from usethis._integrations.uv.deps import Dependency, add_deps_to_group
from usethis._test import change_cwd
from usethis._tool import (
    ALL_TOOLS,
    ConfigEntry,
    ConfigItem,
    ConfigSpec,
    DeptryTool,
    ImportLinterTool,
    PyprojectFmtTool,
    PyprojectTOMLTool,
    RequirementsTxtTool,
    RuffTool,
    Tool,
)


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
                            keys=["tool", self.name], get_value=lambda: {"key": "value"}
                        )
                    }
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

    class TestGetConfigSpec:
        def test_default(self):
            # Arrange
            tool = DefaultTool()

            # Act
            config_spec = tool.get_config_spec()

            # Assert
            assert config_spec == ConfigSpec(
                file_manager_by_relative_path={},
                resolution="first",
                config_items=[],
            )

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
                assert get_hook_ids() == ["ruff", "ruff-format", "deptry"]

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
                assert "deptry" in get_hook_ids()

        def test_dont_add_if_already_present(
            self,
            tmp_path: Path,
            capfd: pytest.CaptureFixture[str],
        ):
            # Arrange
            tool = MyTool()

            # Create a pre-commit config file with one hook
            contents = """\
repos:
  - repo: local
    hooks:
      - id: deptry
        entry: echo "different now!"
"""

            (tmp_path / ".pre-commit-config.yaml").write_text(contents)

            # Act
            with change_cwd(tmp_path):
                tool.add_pre_commit_repo_configs()

                # Assert
                out, err = capfd.readouterr()
                assert not err
                assert not out
                assert get_hook_ids() == ["deptry"]

        def test_ignore_case_sensitivity(
            self,
            tmp_path: Path,
            capfd: pytest.CaptureFixture[str],
        ):
            # Arrange
            tool = MyTool()

            # Create a pre-commit config file with one hook
            contents = """\
repos:
  - repo: local
    hooks:
      - id: Deptry
        entry: echo "different now!"
"""

            (tmp_path / ".pre-commit-config.yaml").write_text(contents)

            # Act
            with change_cwd(tmp_path):
                tool.add_pre_commit_repo_configs()

                # Assert
                out, err = capfd.readouterr()
                assert not err
                assert not out
                assert get_hook_ids() == ["Deptry"]

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
                assert get_hook_ids() == ["ruff", "ruff-format"]

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
                assert get_hook_ids() == ["ruff-format"]
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
                assert get_hook_ids() == ["ruff-format"]
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
                assert get_hook_ids() == [_PLACEHOLDER_ID]

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
                assert get_hook_ids() == [_PLACEHOLDER_ID]

    class TestAddConfigs:
        def test_no_config(self, tmp_path: Path):
            # Arrange
            class NoConfigTool(Tool):
                @property
                def name(self) -> str:
                    return "no_config_tool"

                def print_how_to_use(self) -> None:
                    box_print("How to use no_config_tool")

            nc_tool = NoConfigTool()

            # Act
            with change_cwd(tmp_path):
                nc_tool.add_configs()

                # Assert
                assert not (tmp_path / "pyproject.toml").exists()

        def test_empty(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
            # Arrange
            class ThisTool(Tool):
                @property
                def name(self) -> str:
                    return "mytool"

                def print_how_to_use(self) -> None:
                    box_print("How to use this_tool")

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
                                        get_value=lambda: {"key": "value"},
                                    )
                                }
                            )
                        ],
                    )

            (tmp_path / "pyproject.toml").write_text("")

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                ThisTool().add_configs()

            # Assert
            assert (
                (tmp_path / "pyproject.toml").read_text()
                == """\
[tool.mytool]
key = "value"
"""
            )
            out, err = capfd.readouterr()
            assert not err
            assert out == "✔ Adding mytool config to 'pyproject.toml'.\n"

        def test_differing_sections(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # https://github.com/nathanjmcdougall/usethis-python/issues/184
            # But needs the force=True argument.

            # Arrange
            class ThisTool(Tool):
                @property
                def name(self) -> str:
                    return "mytool"

                def print_how_to_use(self) -> None:
                    box_print("How to use this_tool")

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
                                        get_value=lambda: {
                                            "name": "Modular Design",
                                            "root_packages": ["example"],
                                        },
                                    )
                                },
                                force=True,
                            )
                        ],
                    )

            (tmp_path / "pyproject.toml").write_text(
                """\
[tool.mytool]
name = "Modular Design"
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                ThisTool().add_configs()

            # Assert
            assert (
                (tmp_path / "pyproject.toml").read_text()
                == """\
[tool.mytool]
name = "Modular Design"
root_packages = ["example"]
"""
            )
            out, err = capfd.readouterr()
            assert not err
            assert out == "✔ Adding mytool config to 'pyproject.toml'.\n"

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

    def test_get_pyproject_id_keys(self):
        """Test that get_pyproject_id_keys returns the correct keys."""
        # Arrange
        tool = DeptryTool()

        # Act
        result = tool.get_config_spec()

        # Assert
        (config_item,) = result.config_items
        config_item: ConfigItem
        assert config_item.root[Path("pyproject.toml")] == ConfigEntry(
            keys=["tool", "deptry"]
        )

    def test_remove_pyproject_configs_removes_deptry_section(self, tmp_path: Path):
        """Test that remove_pyproject_configs removes the deptry section."""
        # Arrange
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""[tool.deptry]
ignore_missing = ["pytest"]
""")

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            tool = DeptryTool()
            tool.remove_configs()

        # Assert
        assert "[tool.deptry]" not in pyproject.read_text()
        assert "ignore_missing" not in pyproject.read_text()

    class TestIsManagedRule:
        def test_dep001(self):
            # Arrange
            rule = "DEP001"

            # Act
            result = DeptryTool().is_managed_rule(rule)

            # Assert
            assert result is True

        def test_not_deptry_rule(self):
            # Arrange
            rule = "NOT_DEPTRY_RULE"

            # Act
            result = DeptryTool().is_managed_rule(rule)

            # Assert
            assert result is False

        def test_extra_letters(self):
            # Arrange
            rule = "DEPA001"

            # Act
            result = DeptryTool().is_managed_rule(rule)

            # Assert
            assert result is False

        def test_leading_numbers(self):
            # Arrange
            rule = "001DEP"

            # Act
            result = DeptryTool().is_managed_rule(rule)

            # Assert
            assert result is False

        def test_letters_separated_by_numbers(self):
            # Arrange
            rule = "D0E0P1"

            # Act
            result = DeptryTool().is_managed_rule(rule)

            # Assert
            assert result is False

        def test_four_numbers(self):
            # Arrange
            rule = "DEP0001"

            # Act
            result = DeptryTool().is_managed_rule(rule)

            # Assert
            assert result is True

        def test_no_numbers(self):
            # Arrange
            rule = "DEP"

            # Act
            result = DeptryTool().is_managed_rule(rule)

            # Assert
            assert result is False

        def test_truncated(self):
            # Arrange
            rule = "DE"

            # Act
            result = DeptryTool().is_managed_rule(rule)

            # Assert
            assert result is False

    class TestSelectRules:
        def test_always_empty(self, tmp_path: Path):
            # Arrange
            tool = DeptryTool()

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                tool.select_rules(["A", "B", "C"])

                # Assert
                assert tool.get_selected_rules() == []

    class TestGetSelectedRules:
        def test_always_empty(self, tmp_path: Path):
            # Arrange
            tool = DeptryTool()

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                result = tool.get_selected_rules()

                # Assert
                assert result == []

    class TestDeselectRules:
        def test_no_effect(self, tmp_path: Path):
            # Arrange
            tool = DeptryTool()

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                tool.deselect_rules(["A", "B", "C"])

                # Assert
                assert tool.get_selected_rules() == []

    class TestIgnoreRules:
        def test_ignore_dep001_no_pyproject_toml(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            tool = DeptryTool()

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                tool.ignore_rules(["DEP001"])

                # Assert
                assert tool.get_ignored_rules() == ["DEP001"]

            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Writing 'pyproject.toml'.\n"
                "✔ Ignoring deptry rule 'DEP001' in 'pyproject.toml'.\n"
            )

        def test_ignore_dep001(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
            # Arrange
            tool = DeptryTool()
            (tmp_path / "pyproject.toml").write_text("")

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                tool.ignore_rules(["DEP001"])

                # Assert
                assert tool.get_ignored_rules() == ["DEP001"]

            assert (
                (tmp_path / "pyproject.toml").read_text()
                == """\
[tool.deptry]
ignore = ["DEP001"]
"""
            )

            out, err = capfd.readouterr()
            assert not err
            assert out == ("✔ Ignoring deptry rule 'DEP001' in 'pyproject.toml'.\n")

    class TestGetIgnoredRules:
        def test_no_pyproject_toml(self, tmp_path: Path):
            # Arrange
            tool = DeptryTool()

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                result = tool.get_ignored_rules()

                # Assert
                assert result == []

        def test_empty(self, tmp_path: Path):
            # Arrange
            tool = DeptryTool()
            (tmp_path / "pyproject.toml").write_text("")

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                result = tool.get_ignored_rules()

                # Assert
                assert result == []

        def test_with_rule(self, tmp_path: Path):
            # Arrange
            tool = DeptryTool()
            (tmp_path / "pyproject.toml").write_text(
                """\
[tool.deptry]
ignore = ["DEP003"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                result = tool.get_ignored_rules()

                # Assert
                assert result == ["DEP003"]


class TestImportLinterTool:
    class TestPrintHowToUse:
        def test_pre_commit_and_uv(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            (tmp_path / "uv.lock").touch()
            (tmp_path / ".pre-commit-config.yaml").touch()

            # Act
            with change_cwd(tmp_path), files_manager():
                ImportLinterTool().print_how_to_use()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "☐ Run 'uv run pre-commit run lint-imports --all-files' to run Import Linter.\n"
            )

        def test_pre_commit_no_uv(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            (tmp_path / ".pre-commit-config.yaml").touch()

            # Act
            with change_cwd(tmp_path), files_manager():
                ImportLinterTool().print_how_to_use()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "☐ Run 'pre-commit run lint-imports --all-files' to run Import Linter.\n"
            )

        def test_uv_only(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
            # Arrange
            (tmp_path / "uv.lock").touch()

            # Act
            with change_cwd(tmp_path), files_manager():
                ImportLinterTool().print_how_to_use()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == ("☐ Run 'uv run lint-imports' to run Import Linter.\n")

        def test_basic(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
            # Act
            with change_cwd(tmp_path), files_manager():
                ImportLinterTool().print_how_to_use()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == ("☐ Run 'lint-imports' to run Import Linter.\n")


class TestPyprojectFmtTool:
    class TestPrintHowToUse:
        def test_uv_only(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
            # Arrange
            (tmp_path / "uv.lock").touch()

            # Act
            with change_cwd(tmp_path), files_manager():
                PyprojectFmtTool().print_how_to_use()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "☐ Run 'uv run pyproject-fmt pyproject.toml' to run pyproject-fmt.\n"
            )


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


class TestRequirementsTxtTool:
    class TestPrintHowToUse:
        def test_pre_commit_and_not_uv(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            (tmp_path / ".pre-commit-config.yaml").touch()

            # Act
            with change_cwd(tmp_path), files_manager():
                RequirementsTxtTool().print_how_to_use()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "☐ Run 'pre-commit run uv-export' to write 'requirements.txt'.\n"
            )


class TestRuffTool:
    class TestSelectRules:
        def test_no_pyproject_toml(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with (
                change_cwd(tmp_path),
                files_manager(),
            ):
                RuffTool().select_rules(["A", "B", "C"])

                # Assert
                assert RuffTool().get_selected_rules() == ["A", "B", "C"]

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Writing 'pyproject.toml'.\n"
                "✔ Enabling Ruff rules 'A', 'B', 'C' in 'pyproject.toml'.\n"
            )

        def test_message(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
            # Arrange
            (tmp_path / "pyproject.toml").write_text("")

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().select_rules(["A", "B", "C"])

            # Assert
            out, _ = capfd.readouterr()
            assert "✔ Enabling Ruff rules 'A', 'B', 'C' in 'pyproject.toml" in out

        def test_blank_slate(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text("")

            # Act
            new_rules = ["A", "B", "C"]
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().select_rules(new_rules)

                # Assert
                rules = RuffTool().get_selected_rules()
            assert rules == new_rules

        def test_mixing(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """
    [tool.ruff.lint]
    select = ["A", "B"]
    """
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().select_rules(["C", "D"])

                # Assert
                rules = RuffTool().get_selected_rules()
            assert rules == ["A", "B", "C", "D"]

        def test_respects_order(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """
[tool.ruff.lint]
select = ["D", "B", "A"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().select_rules(["E", "C", "A"])

                # Assert
                assert RuffTool().get_selected_rules() == ["D", "B", "A", "C", "E"]

        def test_ruff_toml(self, tmp_path: Path):
            # Arrange
            (tmp_path / "ruff.toml").write_text(
                """
[lint]
select = ["A", "B"]
"""
            )

            # Act
            with change_cwd(tmp_path), RuffTOMLManager():
                RuffTool().select_rules(["C", "D"])

                # Assert
                rules = RuffTool().get_selected_rules()

            assert rules == ["A", "B", "C", "D"]

        def test_no_rules(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """
[tool.ruff.lint]
select = ["A"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().select_rules([])

                # Assert
                assert RuffTool().get_selected_rules() == ["A"]

    class TestDeselectRules:
        def test_no_pyproject_toml(
            self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Act
            with change_cwd(tmp_path), files_manager():
                RuffTool().deselect_rules(["A"])

                # Assert
                assert RuffTool().get_selected_rules() == []

        def test_blank_slate(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text("")

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().deselect_rules(["A", "B", "C"])

                # Assert
                assert RuffTool().get_selected_rules() == []

        def test_single_rule(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """
[tool.ruff.lint]
select = ["A"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().deselect_rules(["A"])

                # Assert
                assert RuffTool().get_selected_rules() == []

        def test_mix(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """
[tool.ruff.lint]
select = ["A", "B", "C"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().deselect_rules(["A", "C"])

                # Assert
                assert RuffTool().get_selected_rules() == ["B"]

        def test_ruff_toml(self, tmp_path: Path):
            # Arrange
            (tmp_path / ".ruff.toml").write_text(
                """\
[lint]
select = ["A", "B"]
"""
            )

            # Act
            with change_cwd(tmp_path), DotRuffTOMLManager():
                RuffTool().deselect_rules(["A"])

                # Assert
                assert RuffTool().get_selected_rules() == ["B"]

    class TestIgnoreRules:
        def test_add_to_existing(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
[tool.ruff.lint]
ignore = ["A", "B"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().ignore_rules(["C", "D"])

                # Assert
                assert RuffTool().get_ignored_rules() == ["A", "B", "C", "D"]

        def test_no_rules(self, tmp_path: Path):
            # Arrange
            (tmp_path / "pyproject.toml").write_text(
                """\
[tool.ruff.lint]
ignore = ["A"]
"""
            )

            # Act
            with change_cwd(tmp_path), PyprojectTOMLManager():
                RuffTool().ignore_rules([])

                # Assert
                assert RuffTool().get_ignored_rules() == ["A"]


class TestAllTools:
    def test_sorted_alphabetically(self):
        names = [tool.name.lower() for tool in ALL_TOOLS]
        assert names == sorted(names)
