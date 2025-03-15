from __future__ import annotations

from abc import abstractmethod
from pathlib import Path
from typing import Any, Literal, Protocol

from pydantic import BaseModel, InstanceOf
from typing_extensions import assert_never

from usethis._console import box_print, info_print, tick_print
from usethis._integrations.ci.bitbucket.anchor import (
    ScriptItemAnchor as BitbucketScriptItemAnchor,
)
from usethis._integrations.ci.bitbucket.schema import Script as BitbucketScript
from usethis._integrations.ci.bitbucket.schema import Step as BitbucketStep
from usethis._integrations.file.pyproject_toml.errors import (
    PyprojectTOMLValueMissingError,
)
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.pre_commit.hooks import add_repo, get_hook_names, remove_hook
from usethis._integrations.pre_commit.schema import (
    FileType,
    FileTypes,
    HookDefinition,
    Language,
    LocalRepo,
    UriRepo,
)
from usethis._integrations.project.layout import get_source_dir_str
from usethis._integrations.uv.deps import (
    Dependency,
    add_deps_to_group,
    is_dep_in_any_group,
    remove_deps_from_group,
)
from usethis._io import KeyValueFileManager


class ConfigSpec(BaseModel):
    """Specification of configuration files for a tool.

    Attributes:
        file_manager_by_path: File managers that handle the configuration files, indexed
                              by the relative path to the file.
        resolution: The resolution strategy for the configuration files.
                    - "first": Using the order in file_managers, the first file found to
                      exist is used. All subsequent files are ignored. If no files are
                      found, the first file in the list is used.
        entries: List of key-value configurations associated with the tool.
    """

    file_manager_by_relative_path: dict[
        Path, InstanceOf[KeyValueFileManager]
    ]  # TODO N.B. the order of keys matters.
    resolution: Literal["first"]
    config_items: list[ConfigItem]  # TODO update docstring


class _NoConfigValue:
    pass


class ConfigEntry(BaseModel):
    """A configuration entry in a config file associated with a tool.

    Attributes:
        id_keys: A sequentially nested sequence of keys giving a single configuration
                 item.
        value: The default value to be placed at the under the key sequence. By default,
               no configuration will be added.

    """

    # TODO docstring is out of date

    keys: list[str]  # TODO update docstring
    value: Any | InstanceOf[_NoConfigValue] = (
        _NoConfigValue()
    )  # TODO if using _NoConfigValue should add a message to the user telling them to add the config.


class ConfigItem(BaseModel):
    """A config item which can potentially live in different files.

    Attributes:
        root: A dictionary mapping the file path to the configuration entry.
        managed: Whether this configuration should be considered managed by only this
                 tool, and therefore whether it should be removed when the tool is
                 removed.
    """

    root: dict[Path, ConfigEntry]
    managed: bool

    @property
    def paths(self) -> set[Path]:
        """Get the absolute paths to the config files associated with this item."""
        return {(Path.cwd() / path).resolve() for path in self.root}


class Tool(Protocol):
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the tool, for display purposes.

        It is assumed that this name is also the name of the Python package associated
        with the tool; if not, make sure to override methods which access this property.
        """

    @abstractmethod
    def print_how_to_use(self) -> None:
        """Print instructions for using the tool.

        This method is called after a tool is added to the project.
        """
        pass

    def get_bitbucket_steps(self) -> list[BitbucketStep]:
        """Get the Bitbucket pipeline step associated with this tool."""
        return []

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        """The tool's development dependencies.

        These should all be considered characteristic of this particular tool.

        Args:
            unconditional: Whether to return all possible dependencies regardless of
                           whether they are relevant to the current project.
        """
        return []

    def get_test_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        """The tool's test dependencies.

        These should all be considered characteristic of this particular tool.

        Args:
            unconditional: Whether to return all possible dependencies regardless of
                           whether they are relevant to the current project.
        """
        return []

    def get_config_spec(self) -> ConfigSpec:
        """Get the configuration specification for this tool.

        This includes the file managers and resolution methodology.
        """
        return ConfigSpec(
            file_manager_by_relative_path={}, resolution="first", config_items=[]
        )

    def get_pre_commit_repos(self) -> list[LocalRepo | UriRepo]:
        """Get the pre-commit repository configurations for the tool."""
        return []

    def get_associated_ruff_rules(self) -> list[str]:
        """Get the Ruff rule codes associated with the tool."""
        return []

    def get_managed_files(self) -> list[Path]:
        """Get (relative) paths to files managed by (solely) this tool."""
        return []

    def is_used(self) -> bool:
        """Whether the tool is being used in the current project.

        Three heuristics are used by default:
        1. Whether any of the tool's characteristic dev dependencies are in the project.
        2. Whether any of the tool's managed files are in the project.
        3. Whether any of the tool's managed config file sections are present.
        """
        for file in self.get_managed_files():
            if file.exists() and file.is_file():
                return True
        for dep in self.get_dev_deps(unconditional=True):
            if is_dep_in_any_group(dep):
                return True
        for dep in self.get_test_deps(unconditional=True):
            if is_dep_in_any_group(dep):
                return True
        config_spec = self.get_config_spec()
        for config_item in config_spec.config_items:
            if not config_item.managed:
                continue

            for path, entry in config_item.root.items():
                file_manager = config_spec.file_manager_by_relative_path[path]
                if file_manager.do_keys_exist(entry.keys):
                    return True

        return False

    def add_dev_deps(self) -> None:
        add_deps_to_group(self.get_dev_deps(), "dev")

    def remove_dev_deps(self) -> None:
        remove_deps_from_group(self.get_dev_deps(unconditional=True), "dev")

    def add_test_deps(self) -> None:
        add_deps_to_group(self.get_test_deps(), "test")

    def remove_test_deps(self) -> None:
        remove_deps_from_group(self.get_test_deps(unconditional=True), "test")

    def add_pre_commit_repo_configs(self) -> None:
        """Add the tool's pre-commit configuration."""
        repos = self.get_pre_commit_repos()

        if not repos:
            return

        # Add the config for this specific tool.
        for repo_config in repos:
            if repo_config.hooks is None:
                continue

            if len(repo_config.hooks) > 1:
                msg = "Multiple hooks in a single repo not yet supported."
                raise NotImplementedError(msg)

            for hook in repo_config.hooks:
                if hook.id not in get_hook_names():
                    # This will remove the placeholder, if present.
                    add_repo(repo_config)

    def remove_pre_commit_repo_configs(self) -> None:
        """Remove the tool's pre-commit configuration.

        If the .pre-commit-config.yaml file does not exist, this method has no effect.
        """
        repo_configs = self.get_pre_commit_repos()

        if not repo_configs:
            return

        for repo_config in repo_configs:
            if repo_config.hooks is None:
                continue

            # Remove the config for this specific tool.
            for hook in repo_config.hooks:
                if hook.id in get_hook_names():
                    remove_hook(hook.id)

    def get_active_config_file_managers(self) -> set[KeyValueFileManager]:
        """Get relative paths to all active configuration files."""
        config_spec = self.get_config_spec()
        resolution = config_spec.resolution
        if resolution == "first":
            for path, file_manager in config_spec.file_manager_by_relative_path.items():
                if path.exists() and path.is_file():
                    return {file_manager}
            # Couldn't find any existing file so use the first file.
            return {next(iter(config_spec.file_manager_by_relative_path.values()))}
        else:
            assert_never(resolution)

    def add_configs(self) -> None:
        """Add the tool's configuration sections."""
        # Rules:
        # 1. We will never add configuration to a config file that is not active.
        # 2. We will never add a child key to a new parent when an existing parent
        #    already exists, even if that parent is in another file.
        # 3. Subject to #2, we will always prefer to place config in higher-priority
        #    config files
        #
        # This gives the algorithm:
        # For each config item, cycle through the active config files.
        # Find an active file (in order of priority) that is applicable to this config
        # item by indexing (if we can't find one there's a problem!)
        # If the config item has no parent keys (flat config), add it to that file.
        # Otherwise, the item has parent keys. Iterate through the keys starting with
        # the root key, each time checking which active, applicable files contain it.
        # If we reach a point where only one such file contains it, add it to that file.
        # Otherwise, if we reach a point where no such files contain it, backtrack one
        # key level (possibly to the root level) and add it to the highest-priority file.
        # Otherwise, we have iterated through all the keys and the section already exists
        # in multiple files, in which case again we should add it to the highest-priority file,
        # although in practice this means that the config has already been added - when
        # we try to add a config section that's already added (in any case), we should
        # pass the function without doing anything.
        # TODO there's a problem with the above. It assumes that there's a single key
        # sequence to iterate over for each config file. But each file is potentially different.
        # One thing we can check is whether they are actually different... if the ConfigEntry
        # objects are the same for each path then there's no issue.
        # But if there are different ConfigEntry objects (or, at least, the objects have
        # different key sequences) then there's no sure-fire way to determine how one
        # will or won't over-ride the other. One heuristic might be to look at key depth
        # (i.e. total number of strings deep we are) but I figure that might break down
        # easily in a case (which I expect to be quite common) where a disambiguating
        # [tool.xyz] section occurs in pyproject.toml which occurs at the root level
        # in a bespoke config file (leading to an off-by-one issue in counting key levels.)
        # This would only arise with esoteric resolution methodologies so maybe we just
        # leave this issue for now and raise NotImplementedEror if this case ever arises.

        active_config_file_managers = self.get_active_config_file_managers()

        first_addition = True
        for config_item in self.get_config_spec().config_items:
            # Filter to just those active config file managers which can manage this
            # config
            file_managers = [
                file_manager
                for file_manager in active_config_file_managers
                if file_manager.path in config_item.paths
            ]

            if not file_managers:
                msg = f"No active config file managers found for one of the '{self.name}' config items"
                raise NotImplementedError(msg)

            config_entries = list(config_item.root.values())
            if len(config_entries) != 1:
                # TODO handle this case too (YAGNI though?!?)
                msg = (
                    "Adding config is not yet supported for the case of multiple "
                    "active config files."
                )
                raise NotImplementedError(msg)

            (entry,) = config_entries

            if isinstance(entry.value, _NoConfigValue):
                # No value to add, so skip this config item.
                continue

            shared_keys = []
            for key in entry.keys:
                shared_keys += key
                new_file_managers = [
                    file_manager
                    for file_manager in file_managers
                    if file_manager.do_keys_exist(shared_keys)
                ]
                if not new_file_managers:
                    break
                file_managers = new_file_managers

            # Now, use the highest-prority file manager to add the config
            (used_file_manager,) = file_managers
            used_file_manager.set_value(
                keys=entry.keys, value=entry.value, exists_ok=True
            )
            if first_addition:
                tick_print(
                    f"Adding {self.name} config to '{used_file_manager.relative_path}'."
                )
                first_addition = False

    def remove_configs(self) -> None:
        """Remove the tool's configuration sections.

        Note, this does not require knowledge of the config file resolution methodology,
        since all files' configs are removed regardless of whether they are in use.
        """
        first_removal = True
        for config_item in self.get_config_spec().config_items:
            if not config_item.managed:
                continue

            for (
                relative_path,
                file_manager,
            ) in self.get_config_spec().file_manager_by_relative_path.items():
                if file_manager.path in config_item.paths:
                    entry = config_item.root[relative_path]
                    try:
                        file_manager.remove_value(keys=entry.keys, missing_ok=False)
                    except PyprojectTOMLValueMissingError:
                        pass
                    else:
                        if first_removal:
                            tick_print(
                                f"Removing {self.name} config from '{relative_path}'."
                            )
                            first_removal = False

    def remove_managed_files(self) -> None:
        """Remove all files managed by this tool.

        This includes any tool-specific files in the project.
        If no files exist, this method has no effect.
        """
        for file in self.get_managed_files():
            if (Path.cwd() / file).exists() and (Path.cwd() / file).is_file():
                tick_print(f"Removing '{file}'.")
                file.unlink()


class CodespellTool(Tool):
    # https://github.com/codespell-project/codespell
    @property
    def name(self) -> str:
        return "Codespell"

    def print_how_to_use(self) -> None:
        if PreCommitTool().is_used():
            box_print(
                "Run 'pre-commit run codespell --all-files' to run the Codespell spellchecker."
            )
        else:
            box_print("Run 'codespell' to run the Codespell spellchecker.")

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return [Dependency(name="codespell")]

    def get_config_spec(self) -> ConfigSpec:
        # https://github.com/codespell-project/codespell?tab=readme-ov-file#using-a-config-file
        value = {
            "ignore-regex": ["[A-Za-z0-9+/]{100,}"],  # Ignore long base64 strings
        }

        return ConfigSpec(
            file_manager_by_relative_path={
                Path("pyproject.toml"): PyprojectTOMLManager(),
                # TODO need to add the other file managers
            },
            resolution="first",
            config_items=[
                ConfigItem(
                    root={
                        # TODO uncomment this
                        # Path(".codespellrc"): ConfigEntry(
                        #     keys=["codespell"], value=value
                        # ),
                        # Path("setup.cfg"): ConfigEntry(keys=["codespell"], value=value),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "codespell"], value=value
                        ),
                    },
                    managed=True,
                )
            ],
        )

    def get_managed_files(self) -> list[Path]:
        return [Path(".codespellrc")]

    def get_pre_commit_repos(self) -> list[LocalRepo | UriRepo]:
        return [
            UriRepo(
                repo="https://github.com/codespell-project/codespell",
                rev="v2.4.1",  # Manually bump this version when necessary
                hooks=[
                    HookDefinition(id="codespell", additional_dependencies=["tomli"])
                ],
            )
        ]

    def get_bitbucket_steps(self) -> list[BitbucketStep]:
        return [
            BitbucketStep(
                name="Run Codespell",
                caches=["uv"],
                script=BitbucketScript(
                    [
                        BitbucketScriptItemAnchor(name="install-uv"),
                        "uv run codespell",
                    ]
                ),
            )
        ]


class CoverageTool(Tool):
    # https://github.com/nedbat/coveragepy

    @property
    def name(self) -> str:
        return "coverage"

    def print_how_to_use(self) -> None:
        if PytestTool().is_used():
            box_print("Run 'pytest --cov' to run your tests with coverage.")
        else:
            box_print("Run 'coverage help' to see available coverage commands.")

    def get_test_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        deps = [Dependency(name="coverage", extras=frozenset({"toml"}))]
        if unconditional or PytestTool().is_used():
            deps += [Dependency(name="pytest-cov")]
        return deps

    def get_config_spec(self) -> ConfigSpec:
        # https://coverage.readthedocs.io/en/7.6.12/config.html#configuration-reference

        run_value = {
            "source": [get_source_dir_str()],
            "omit": ["*/pytest-of-*/*"],
        }
        report_value = {
            "exclude_also": [
                "if TYPE_CHECKING:",
                "raise AssertionError",
                "raise NotImplementedError",
                "assert_never(.*)",
                "class .*\\bProtocol\\):",
                "@(abc\\.)?abstractmethod",
            ]
        }

        return ConfigSpec(
            file_manager_by_relative_path={
                Path("pyproject.toml"): PyprojectTOMLManager(),
                # TODO need to add the other file managers
            },
            resolution="first",
            config_items=[
                ConfigItem(
                    root={
                        # TODO uncomment these
                        # Path(".coveragerc"): ConfigEntry(keys=["run"], value=run_value),
                        # Path("setup.cfg"): ConfigEntry(
                        #     keys=["coverage:run"], value=run_value
                        # ),
                        # Path("tox.ini"): ConfigEntry(  # TODO github issue for tox?
                        #     keys=["coverage:run"], value=run_value
                        # ),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "run"], value=run_value
                        ),
                    },
                    managed=True,
                ),
                ConfigItem(
                    # TODO uncomment this out.
                    root={
                        # Path(".coveragerc"): ConfigEntry(
                        #     keys=["report"], value=report_value
                        # ),
                        # Path("setup.cfg"): ConfigEntry(
                        #     keys=["coverage:report"], value=report_value
                        # ),
                        # Path("tox.ini"): ConfigEntry(
                        #     keys=["coverage:report"], value=report_value
                        # ),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "report"], value=report_value
                        ),
                    },
                    managed=True,
                ),
            ],
        )

    def get_managed_files(self) -> list[Path]:
        return [Path(".coveragerc")]


class DeptryTool(Tool):
    # https://github.com/fpgmaas/deptry
    @property
    def name(self) -> str:
        return "deptry"

    def print_how_to_use(self) -> None:
        _dir = get_source_dir_str()
        box_print(f"Run 'deptry {_dir}' to run deptry.")

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return [Dependency(name="deptry")]

    def get_config_spec(self) -> ConfigSpec:
        # https://deptry.com/usage/#configuration
        return ConfigSpec(
            file_manager_by_relative_path={
                Path("pyproject.toml"): PyprojectTOMLManager(),
            },
            resolution="first",
            # TODO also when would we actually ever specify a non-managed config? Need to document this. I guess it would be if we are configuring other tools.
            config_items=[
                ConfigItem(
                    root={Path("pyproject.toml"): ConfigEntry(keys=["tool", "deptry"])},
                    managed=True,
                )
            ],
        )

    def get_pre_commit_repos(self) -> list[LocalRepo | UriRepo]:
        _dir = get_source_dir_str()
        return [
            LocalRepo(
                repo="local",
                hooks=[
                    HookDefinition(
                        id="deptry",
                        name="deptry",
                        entry=f"uv run --frozen --offline deptry {_dir}",
                        language=Language("system"),
                        always_run=True,
                        pass_filenames=False,
                    )
                ],
            )
        ]

    def get_bitbucket_steps(self) -> list[BitbucketStep]:
        _dir = get_source_dir_str()
        return [
            BitbucketStep(
                name="Run Deptry",
                caches=["uv"],
                script=BitbucketScript(
                    [
                        BitbucketScriptItemAnchor(name="install-uv"),
                        f"uv run deptry {_dir}",
                    ]
                ),
            )
        ]


class PreCommitTool(Tool):
    # https://github.com/pre-commit/pre-commit
    @property
    def name(self) -> str:
        return "pre-commit"

    def print_how_to_use(self) -> None:
        box_print("Run 'pre-commit run --all-files' to run the hooks manually.")

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return [Dependency(name="pre-commit")]

    def get_managed_files(self) -> list[Path]:
        return [Path(".pre-commit-config.yaml")]

    def get_bitbucket_steps(self) -> list[BitbucketStep]:
        return [
            BitbucketStep(
                name="Run pre-commit",
                caches=["uv", "pre-commit"],
                script=BitbucketScript(
                    [
                        BitbucketScriptItemAnchor(name="install-uv"),
                        "uv run pre-commit run --all-files",
                    ]
                ),
            )
        ]


class PyprojectFmtTool(Tool):
    # https://github.com/tox-dev/pyproject-fmt
    @property
    def name(self) -> str:
        return "pyproject-fmt"

    def print_how_to_use(self) -> None:
        if PreCommitTool().is_used():
            box_print(
                "Run 'pre-commit run pyproject-fmt --all-files' to run pyproject-fmt."
            )
        else:
            box_print("Run 'pyproject-fmt pyproject.toml' to run pyproject-fmt.")

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return [Dependency(name="pyproject-fmt")]

    def get_config_spec(self) -> ConfigSpec:
        # https://pyproject-fmt.readthedocs.io/en/latest/#configuration-via-file
        return ConfigSpec(
            file_manager_by_relative_path={
                Path("pyproject.toml"): PyprojectTOMLManager(),
            },
            resolution="first",
            config_items=[
                ConfigItem(
                    root={
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "pyproject-fmt"],
                            value={"keep_full_version": True},
                        )
                    },
                    managed=True,
                )
            ],
        )

    def get_pre_commit_repos(self) -> list[LocalRepo | UriRepo]:
        return [
            UriRepo(
                repo="https://github.com/tox-dev/pyproject-fmt",
                rev="v2.5.0",  # Manually bump this version when necessary
                hooks=[HookDefinition(id="pyproject-fmt")],
            )
        ]

    def get_bitbucket_steps(self) -> list[BitbucketStep]:
        return [
            BitbucketStep(
                name="Run pyproject-fmt",
                caches=["uv"],
                script=BitbucketScript(
                    [
                        BitbucketScriptItemAnchor(name="install-uv"),
                        "uv run pyproject-fmt pyproject.toml",
                    ]
                ),
            )
        ]


class PyprojectTOMLTool(Tool):
    # https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
    @property
    def name(self) -> str:
        return "pyproject.toml"

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return []

    def print_how_to_use(self) -> None:
        box_print("Populate 'pyproject.toml' with the project configuration.")
        info_print(
            "Learn more at https://packaging.python.org/en/latest/guides/writing-pyproject-toml/"
        )

    def get_managed_files(self) -> list[Path]:
        return [
            Path("pyproject.toml"),
        ]


class PytestTool(Tool):
    # https://github.com/pytest-dev/pytest
    @property
    def name(self) -> str:
        return "pytest"

    def print_how_to_use(self) -> None:
        box_print(
            "Add test files to the '/tests' directory with the format 'test_*.py'."
        )
        box_print("Add test functions with the format 'test_*()'.")
        box_print("Run 'pytest' to run the tests.")

    def get_test_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        deps = [Dependency(name="pytest")]
        if unconditional or CoverageTool().is_used():
            deps += [Dependency(name="pytest-cov")]
        return deps

    def get_config_spec(self) -> ConfigSpec:
        # https://docs.pytest.org/en/stable/reference/customize.html#configuration-file-formats
        # "Options from multiple configfiles candidates are never merged - the first match wins."

        # Much of what follows is recommended here (sp-repo-review):
        # https://learn.scientific-python.org/development/guides/pytest/#configuring-pytest
        value = {
            "testpaths": ["tests"],
            "addopts": [
                "--import-mode=importlib",  # Now recommended https://docs.pytest.org/en/7.1.x/explanation/goodpractices.html#which-import-mode
                "-ra",  # summary report of all results (sp-repo-review)
                "--showlocals",  # print locals in tracebacks (sp-repo-review)
                "--strict-markers",  # fail on unknown markers (sp-repo-review)
                "--strict-config",  # fail on unknown config (sp-repo-review)
            ],
            "filterwarnings": ["error"],  # fail on warnings (sp-repo-review)
            "xfail_strict": True,  # fail on tests marked xfail (sp-repo-review)
            "log_cli_level": "INFO",  # include all >=INFO level log messages (sp-repo-review)
            "minversion": "7",  # minimum pytest version (sp-repo-review)
        }

        return ConfigSpec(
            file_manager_by_relative_path={
                Path("pyproject.toml"): PyprojectTOMLManager(),
                # TODO need to add the other file managers
            },
            resolution="first",
            config_items=[
                ConfigItem(
                    root={
                        # TODO uncomment these
                        # Path("pytest.ini"): ConfigEntry(keys=["pytest"], value=value),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "pytest", "ini_options"], value=value
                        ),
                        # Path("tox.ini"): ConfigEntry(keys=["pytest"], value=value),
                        # Path("setup.cfg"): ConfigEntry(
                        #     keys=["tool:pytest"], value=value
                        # ),
                    },
                    managed=True,
                ),
                ConfigItem(
                    root={
                        Path("pyproject.toml"): ConfigEntry(keys=["tool", "pytest"])
                    },  # TODO need to test and add this for other managed tools etc.
                    # TODO also need to add this for other files (for all tools!) etc.
                    managed=True,
                ),
            ],
        )

    def get_managed_files(self) -> list[Path]:
        return [Path("pytest.ini"), Path("tests/conftest.py")]

    def get_extra_dev_deps(self) -> list[Dependency]:
        return [Dependency(name="pytest-cov")]

    def get_associated_ruff_rules(self) -> list[str]:
        return ["PT"]


class RequirementsTxtTool(Tool):
    # https://pip.pypa.io/en/stable/reference/requirements-file-format/

    @property
    def name(self) -> str:
        return "requirements.txt"

    def print_how_to_use(self) -> None:
        if PreCommitTool().is_used():
            box_print("Run the 'pre-commit run uv-export' to write 'requirements.txt'.")
        else:
            box_print(
                "Run 'uv export --no-dev -o=requirements.txt' to write 'requirements.txt'."
            )

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return []

    def get_managed_files(self) -> list[Path]:
        return [Path("requirements.txt")]

    def get_pre_commit_repos(self) -> list[LocalRepo | UriRepo]:
        return [
            LocalRepo(
                repo="local",
                hooks=[
                    HookDefinition(
                        id="uv-export",
                        name="uv-export",
                        files="^uv\\.lock$",
                        pass_filenames=False,
                        entry="uv export --frozen --offline --quiet --no-dev -o=requirements.txt",
                        language=Language("system"),
                        require_serial=True,
                    )
                ],
            )
        ]


class RuffTool(Tool):
    # https://github.com/astral-sh/ruff
    @property
    def name(self) -> str:
        return "Ruff"

    def print_how_to_use(self) -> None:
        box_print("Run 'ruff check --fix' to run the Ruff linter with autofixes.")
        box_print("Run 'ruff format' to run the Ruff formatter.")

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return [Dependency(name="ruff")]

    def get_config_spec(self) -> ConfigSpec:
        # https://docs.astral.sh/ruff/configuration/#config-file-discovery

        value = {
            "line-length": 88,
            "lint": {"select": []},
        }

        return ConfigSpec(
            file_manager_by_relative_path={
                # TODO need to uncomment these and give their own file manager.
                # Can this be set up to avoid duplicated shallow class definition
                # Path(".ruff.toml"): TOMLFileManager(),
                # Path("ruff.toml"): TOMLFileManager(),
                Path("pyproject.toml"): PyprojectTOMLManager(),
            },
            resolution="first",
            config_items=[
                ConfigItem(
                    root={
                        # TODO test that empty key works and puts at root
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "ruff"], value=value
                        ),
                        # TODO uncomment
                        # Path(".ruff.toml"): ConfigEntry(keys=[], value=value),
                        # Path("ruff.toml"): ConfigEntry(keys=[], value=value),
                    },
                    managed=True,
                )
            ],
        )

    def get_managed_files(self) -> list[Path]:
        return [Path(".ruff.toml"), Path("ruff.toml")]

    def get_pre_commit_repos(self) -> list[LocalRepo | UriRepo]:
        return [
            LocalRepo(
                repo="local",
                hooks=[
                    HookDefinition(
                        id="ruff-format",
                        name="ruff-format",
                        entry="uv run --frozen --offline ruff format --force-exclude",
                        language=Language("system"),
                        types_or=FileTypes(
                            [FileType("python"), FileType("pyi"), FileType("jupyter")]
                        ),
                        always_run=True,
                        require_serial=True,
                    ),
                ],
            ),
            LocalRepo(
                repo="local",
                hooks=[
                    HookDefinition(
                        id="ruff",
                        name="ruff",
                        entry="uv run --frozen --offline ruff check --fix --force-exclude",
                        language=Language("system"),
                        types_or=FileTypes(
                            [FileType("python"), FileType("pyi"), FileType("jupyter")]
                        ),
                        always_run=True,
                        require_serial=True,
                    ),
                ],
            ),
        ]

    def get_bitbucket_steps(self) -> list[BitbucketStep]:
        return [
            BitbucketStep(
                name="Run Ruff",
                caches=["uv"],
                script=BitbucketScript(
                    [
                        BitbucketScriptItemAnchor(name="install-uv"),
                        "uv run ruff check --fix",
                        "uv run ruff format",
                    ]
                ),
            )
        ]


ALL_TOOLS: list[Tool] = [
    CodespellTool(),
    CoverageTool(),
    DeptryTool(),
    PreCommitTool(),
    PyprojectTOMLTool(),
    PyprojectFmtTool(),
    PytestTool(),
    RequirementsTxtTool(),
    RuffTool(),
]
