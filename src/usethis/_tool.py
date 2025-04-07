from __future__ import annotations

import re
from abc import abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal, Protocol, TypeAlias

from pydantic import BaseModel, InstanceOf
from typing_extensions import Self, assert_never

from usethis._config_file import (
    CodespellRCManager,
    CoverageRCManager,
    DotImportLinterManager,
    DotPytestINIManager,
    DotRuffTOMLManager,
    PytestINIManager,
    RuffTOMLManager,
    ToxINIManager,
)
from usethis._console import box_print, info_print, tick_print, warn_print
from usethis._integrations.ci.bitbucket.anchor import (
    ScriptItemAnchor as BitbucketScriptItemAnchor,
)
from usethis._integrations.ci.bitbucket.schema import Script as BitbucketScript
from usethis._integrations.ci.bitbucket.schema import Step as BitbucketStep
from usethis._integrations.ci.bitbucket.steps import (
    _steps_are_equivalent,
    add_bitbucket_step_in_default,
    get_steps_in_default,
    remove_bitbucket_step_from_default,
)
from usethis._integrations.ci.bitbucket.used import is_bitbucket_used
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.file.setup_cfg.io_ import SetupCFGManager
from usethis._integrations.pre_commit.hooks import (
    _hook_ids_are_equivalent,
    add_repo,
    get_hook_ids,
    remove_hook,
)
from usethis._integrations.pre_commit.schema import (
    FileType,
    FileTypes,
    HookDefinition,
    Language,
    LocalRepo,
    UriRepo,
)
from usethis._integrations.project.errors import ImportGraphBuildFailedError
from usethis._integrations.project.imports import (
    LayeredArchitecture,
    get_layered_architectures,
)
from usethis._integrations.project.layout import get_source_dir_str
from usethis._integrations.project.name import get_project_name
from usethis._integrations.project.packages import get_importable_packages
from usethis._integrations.uv.deps import (
    Dependency,
    add_deps_to_group,
    is_dep_in_any_group,
    remove_deps_from_group,
)
from usethis._integrations.uv.init import ensure_pyproject_toml
from usethis._integrations.uv.python import get_supported_major_python_versions
from usethis._integrations.uv.used import is_uv_used
from usethis._io import KeyValueFileManager

ResolutionT: TypeAlias = Literal["first", "bespoke"]


class ConfigSpec(BaseModel):
    """Specification of configuration files for a tool.

    Attributes:
        file_manager_by_relative_path: File managers that handle the configuration
                                       files, indexed by the relative path to the file.
                                       The order of the keys matters, as it determines
                                       the resolution order; the earlier occurring keys
                                       take precedence over later ones. All file
                                       managers used in the config items must be keys.
        resolution: The resolution strategy for the configuration files.
                    - "first": Using the order in file_managers, the first file found to
                      exist is used. All subsequent files are ignored. If no files are
                      found, the first file in the list is used.
        config_items: A list of configuration items that can be managed by the tool.
    """

    file_manager_by_relative_path: dict[Path, InstanceOf[KeyValueFileManager]]
    resolution: ResolutionT
    config_items: list[ConfigItem]

    @classmethod
    def from_flat(
        cls,
        file_managers: list[KeyValueFileManager],
        resolution: ResolutionT,
        config_items: list[ConfigItem],
    ) -> Self:
        file_manager_by_relative_path = {
            file_manager.relative_path: file_manager for file_manager in file_managers
        }

        return cls(
            file_manager_by_relative_path=file_manager_by_relative_path,
            resolution=resolution,
            config_items=config_items,
        )


class _NoConfigValue:
    pass


def _get_no_config_value() -> _NoConfigValue:
    return _NoConfigValue()


class ConfigEntry(BaseModel):
    """A configuration entry in a config file associated with a tool.

    Attributes:
        keys: A sequentially nested sequence of keys giving a single configuration item.
        value: The default value to be placed at the under the key sequence. By default,
               no configuration will be added, which is most appropriate for top-level
               configuration sections like [tool.usethis] under which the entire tool's
               config gets placed.

    """

    keys: list[str]
    get_value: Callable[[], Any] = _get_no_config_value


class ConfigItem(BaseModel):
    """A config item which can potentially live in different files.

    Attributes:
        description: An annotation explaining the meaning of what the config represents.
                     This is purely for documentation and is optional.
        root: A dictionary mapping the file path to the configuration entry.
        managed: Whether this configuration should be considered managed by only this
                 tool, and therefore whether it should be removed when the tool is
                 removed. This might be set to False if we are modifying other tools'
                 config sections or shared config sections that are pre-requisites for
                 using this tool but might be relied on by other tools as well.
        force: Whether to overwrite any existing configuration entry. Defaults to false,
               in which case existing configuration is left as-is for the entry.
        applies_to_all: Whether all file managers should support this config item, or
                        whether it is optional and is only desirable if we know in
                        advance what the file managers are which are being used.
                        Defaults to True, which means a NotImplementedError will be
                        raised if a file manager does not support this config item.
                        It is useful to set this to False when the config item
                        corresponds to the root level config, which isn't always
                        available for non-nested file types like INI. For example,
                        we might have the [tool.coverage] section in pyproject.toml
                        but in tox.ini we have [coverage:run] and [coverage:report]
                        but no overall root [coverage] section.
    """

    description: str | None = None
    root: dict[Path, ConfigEntry]
    managed: bool = True
    force: bool = False
    applies_to_all: bool = True

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
                if entry.keys in file_manager:
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
                if not any(
                    _hook_ids_are_equivalent(hook.id, hook_id)
                    for hook_id in get_hook_ids()
                ):
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
                if hook.id in get_hook_ids():
                    remove_hook(hook.id)

    def get_active_config_file_managers(self) -> set[KeyValueFileManager]:
        """Get relative paths to all active configuration files."""
        config_spec = self.get_config_spec()
        resolution = config_spec.resolution
        if resolution == "first":
            # N.B. keep this roughly in sync with the bespoke logic for pytest
            for (
                relative_path,
                file_manager,
            ) in config_spec.file_manager_by_relative_path.items():
                path = Path.cwd() / relative_path
                if path.exists() and path.is_file():
                    return {file_manager}

            file_managers = config_spec.file_manager_by_relative_path.values()
            if not file_managers:
                return set()

            # Use the preferred default file since there's no existing file.
            preferred_file_manager = self.preferred_file_manager()
            if preferred_file_manager not in file_managers:
                msg = (
                    f"The preferred file manager '{preferred_file_manager}' is not "
                    f"among the file managers '{file_managers}' for the tool "
                    f"'{self.name}'"
                )
                raise NotImplementedError(msg)
            return {preferred_file_manager}
        elif resolution == "bespoke":
            msg = (
                "The bespoke resolution method is not yet implemented for the tool "
                f"{self.name}."
            )
            raise NotImplementedError(msg)
        else:
            assert_never(resolution)

    def preferred_file_manager(self) -> KeyValueFileManager:
        """If there is no currently active config file, this is the preferred one."""
        return PyprojectTOMLManager()

    def add_configs(self) -> None:
        """Add the tool's configuration sections."""
        # Principles:
        # 1. We will never add configuration to a config file that is not active.
        # 2. We will never add a child key to a new parent when an existing parent
        #    already exists, even if that parent is in another file.
        # 3. Subject to #2, we will always prefer to place config in higher-priority
        #    config files.
        # In practice, the most common resolution method is "first", in which case there
        # is only ever one active file; so principles #2 and #3 are not relevant.

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
                if config_item.applies_to_all:
                    msg = f"No active config file managers found for one of the '{self.name}' config items"
                    raise NotImplementedError(msg)
                else:
                    # Early exist; this config item is not managed by any active files
                    # so it's optional, effectively.
                    continue

            config_entries = [
                config_item
                for relative_path, config_item in config_item.root.items()
                if relative_path
                in {file_manager.relative_path for file_manager in file_managers}
            ]
            if not config_entries:
                msg = (
                    f"No config entries found for one of the '{self.name}' config items"
                )
                raise NotImplementedError(msg)
            if len(config_entries) != 1:
                msg = (
                    "Adding config is not yet supported for the case of multiple "
                    "active config files."
                )
                raise NotImplementedError(msg)

            (entry,) = config_entries

            if isinstance(entry.get_value(), _NoConfigValue):
                # No value to add, so skip this config item.
                continue

            shared_keys = []
            for key in entry.keys:
                shared_keys.append(key)
                new_file_managers = [
                    file_manager
                    for file_manager in file_managers
                    if shared_keys in file_manager
                ]
                if not new_file_managers:
                    break
                file_managers = new_file_managers

            # Now, use the highest-prority file manager to add the config
            (used_file_manager,) = file_managers

            if not config_item.force and entry.keys in used_file_manager:
                # We won't overwrite, so skip if there is already a value set.
                continue

            if first_addition:
                tick_print(
                    f"Adding {self.name} config to '{used_file_manager.relative_path}'."
                )
                first_addition = False
            used_file_manager[entry.keys] = entry.get_value()

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
                    if not (file_manager.path.exists() and file_manager.path.is_file()):
                        # This is mostly for the sake of the first_removal message
                        continue

                    entry = config_item.root[relative_path]
                    try:
                        del file_manager[entry.keys]
                    except KeyError:
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

    def get_bitbucket_steps(self) -> list[BitbucketStep]:
        """Get the Bitbucket pipeline step associated with this tool."""
        return []

    def get_managed_bitbucket_step_names(self) -> list[str]:
        """These are the names of the Bitbucket steps that are managed by this tool.

        They should be removed if they are not currently active according to `get_bitbucket_steps`.
        They should also be removed if the tool is removed.
        """
        return [
            step.name for step in self.get_bitbucket_steps() if step.name is not None
        ]

    def remove_bitbucket_steps(self) -> None:
        """Remove the Bitbucket steps associated with this tool."""
        for step in get_steps_in_default():
            if step.name in self.get_managed_bitbucket_step_names():
                remove_bitbucket_step_from_default(step)

    def update_bitbucket_steps(self) -> None:
        """Add Bitbucket steps associated with this tool, and remove outdated ones.

        Only runs if Bitbucket is used in the project.
        """
        if not is_bitbucket_used() or not self.is_used():
            return

        # Add the new steps
        for step in self.get_bitbucket_steps():
            add_bitbucket_step_in_default(step)

        # Remove any old steps that are not active managed by this tool
        for step in get_steps_in_default():
            if step.name in self.get_managed_bitbucket_step_names() and not any(
                _steps_are_equivalent(step, step_)
                for step_ in self.get_bitbucket_steps()
            ):
                remove_bitbucket_step_from_default(step)

    def get_associated_ruff_rules(self) -> list[str]:
        """Get the Ruff rule codes associated with the tool.

        These are managed rules and it is assumed that they can be removed if the tool
        is removed. It only makes sense to include rules which are tightly bound
        with the tool.
        """
        # For other rules which are not tightly bound to the tool, see
        # https://github.com/nathanjmcdougall/usethis-python/issues/499
        return []

    def is_managed_rule(self, rule: str) -> bool:
        """Determine if a rule is managed by this tool."""
        return False

    def select_rules(self, rules: list[str]) -> None:
        """Select the rules managed by the tool.

        These rules are not validated; it is assumed they are valid rules for the tool,
        and that the tool will be able to manage them.
        """

    def get_selected_rules(self) -> list[str]:
        """Get the rules managed by the tool that are currently selected."""
        return []

    def ignore_rules(self, rules: list[str]) -> None:
        """Ignore rules managed by the tool.

        Ignoring a rule is different from deselecting it - it means that even if it
        selected, it will not take effect. See the way that Ruff configuration works to
        understand this concept in more detail.

        These rules are not validated; it is assumed they are valid rules for the tool,
        and that the tool will be able to manage them.
        """

    def get_ignored_rules(self) -> list[str]:
        """Get the ignored rules managed by the tool."""
        return []

    def deselect_rules(self, rules: list[str]) -> None:
        """Deselect the rules managed by the tool.

        Any rules that aren't already selected are ignored.
        """


class CodespellTool(Tool):
    # https://github.com/codespell-project/codespell
    @property
    def name(self) -> str:
        return "Codespell"

    def print_how_to_use(self) -> None:
        if PreCommitTool().is_used():
            if is_uv_used():
                box_print(
                    "Run 'uv run pre-commit run codespell --all-files' to run the Codespell spellchecker."
                )
            else:
                box_print(
                    "Run 'pre-commit run codespell --all-files' to run the Codespell spellchecker."
                )
        elif is_uv_used():
            box_print("Run 'uv run codespell' to run the Codespell spellchecker.")
        else:
            box_print("Run 'codespell' to run the Codespell spellchecker.")

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return [Dependency(name="codespell")]

    def get_config_spec(self) -> ConfigSpec:
        # https://github.com/codespell-project/codespell?tab=readme-ov-file#using-a-config-file

        return ConfigSpec.from_flat(
            file_managers=[
                CodespellRCManager(),
                SetupCFGManager(),
                PyprojectTOMLManager(),
            ],
            resolution="first",
            config_items=[
                ConfigItem(
                    description="Overall config",
                    root={
                        Path(".codespellrc"): ConfigEntry(keys=[]),
                        Path("setup.cfg"): ConfigEntry(keys=["codespell"]),
                        Path("pyproject.toml"): ConfigEntry(keys=["tool", "codespell"]),
                    },
                ),
                ConfigItem(
                    description="Ignore long base64 strings",
                    root={
                        Path(".codespellrc"): ConfigEntry(
                            keys=["codespell", "ignore-regex"],
                            get_value=lambda: "[A-Za-z0-9+/]{100,}",
                        ),
                        Path("setup.cfg"): ConfigEntry(
                            keys=["codespell", "ignore-regex"],
                            get_value=lambda: "[A-Za-z0-9+/]{100,}",
                        ),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "codespell", "ignore-regex"],
                            get_value=lambda: ["[A-Za-z0-9+/]{100,}"],
                        ),
                    },
                ),
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
                name=f"Run {self.name}",
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
            if is_uv_used():
                box_print("Run 'uv run pytest --cov' to run your tests with coverage.")
            else:
                box_print("Run 'pytest --cov' to run your tests with coverage.")
        elif is_uv_used():
            box_print("Run 'uv run coverage help' to see available coverage commands.")
        else:
            box_print("Run 'coverage help' to see available coverage commands.")

    def get_test_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        deps = [Dependency(name="coverage", extras=frozenset({"toml"}))]
        if unconditional or PytestTool().is_used():
            deps += [Dependency(name="pytest-cov")]
        return deps

    def get_config_spec(self) -> ConfigSpec:
        # https://coverage.readthedocs.io/en/latest/config.html#configuration-reference

        exclude_also = [
            "if TYPE_CHECKING:",
            "raise AssertionError",
            "raise NotImplementedError",
            "assert_never(.*)",
            "class .*\\bProtocol\\):",
            "@(abc\\.)?abstractmethod",
        ]
        omit = ["*/pytest-of-*/*"]

        def _get_source():
            return [get_source_dir_str()]

        return ConfigSpec.from_flat(
            file_managers=[
                CoverageRCManager(),
                SetupCFGManager(),
                ToxINIManager(),
                PyprojectTOMLManager(),
            ],
            resolution="first",
            config_items=[
                ConfigItem(
                    description="Overall Config",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=[]),
                        # N.B. other ini files use a "coverage:" prefix so there's no
                        # section corresponding to overall config
                        Path("pyproject.toml"): ConfigEntry(keys=["tool", "coverage"]),
                    },
                    applies_to_all=False,
                ),
                ConfigItem(
                    description="Run Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=["run"]),
                        Path("setup.cfg"): ConfigEntry(keys=["coverage:run"]),
                        Path("tox.ini"): ConfigEntry(keys=["coverage:run"]),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "run"]
                        ),
                    },
                ),
                ConfigItem(
                    description="Source Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(
                            keys=["run", "source"], get_value=_get_source
                        ),
                        Path("setup.cfg"): ConfigEntry(
                            keys=["coverage:run", "source"], get_value=_get_source
                        ),
                        Path("tox.ini"): ConfigEntry(
                            keys=["coverage:run", "source"], get_value=_get_source
                        ),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "run", "source"],
                            get_value=_get_source,
                        ),
                    },
                ),
                ConfigItem(
                    description="Report Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=["report"]),
                        Path("setup.cfg"): ConfigEntry(keys=["coverage:report"]),
                        Path("tox.ini"): ConfigEntry(keys=["coverage:report"]),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "report"]
                        ),
                    },
                ),
                ConfigItem(
                    description="Exclude Also Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(
                            keys=["report", "exclude_also"],
                            get_value=lambda: exclude_also,
                        ),
                        Path("setup.cfg"): ConfigEntry(
                            keys=["coverage:report", "exclude_also"],
                            get_value=lambda: exclude_also,
                        ),
                        Path("tox.ini"): ConfigEntry(
                            keys=["coverage:report", "exclude_also"],
                            get_value=lambda: exclude_also,
                        ),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "report", "exclude_also"],
                            get_value=lambda: exclude_also,
                        ),
                    },
                ),
                ConfigItem(
                    description="Omit Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(
                            keys=["report", "omit"], get_value=lambda: omit
                        ),
                        Path("setup.cfg"): ConfigEntry(
                            keys=["coverage:report", "omit"], get_value=lambda: omit
                        ),
                        Path("tox.ini"): ConfigEntry(
                            keys=["coverage:report", "omit"], get_value=lambda: omit
                        ),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "report", "omit"],
                            get_value=lambda: omit,
                        ),
                    },
                ),
                ConfigItem(
                    description="Paths Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=["paths"]),
                        Path("setup.cfg"): ConfigEntry(keys=["coverage:paths"]),
                        Path("tox.ini"): ConfigEntry(keys=["coverage:paths"]),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "paths"],
                        ),
                    },
                ),
                ConfigItem(
                    description="HTML Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=["html"]),
                        Path("setup.cfg"): ConfigEntry(keys=["coverage:html"]),
                        Path("tox.ini"): ConfigEntry(keys=["coverage:html"]),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "html"]
                        ),
                    },
                ),
                ConfigItem(
                    description="XML Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=["xml"]),
                        Path("setup.cfg"): ConfigEntry(keys=["coverage:xml"]),
                        Path("tox.ini"): ConfigEntry(keys=["coverage:xml"]),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "xml"]
                        ),
                    },
                ),
                ConfigItem(
                    description="JSON Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=["json"]),
                        Path("setup.cfg"): ConfigEntry(keys=["coverage:json"]),
                        Path("tox.ini"): ConfigEntry(keys=["coverage:json"]),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "json"]
                        ),
                    },
                ),
                ConfigItem(
                    description="LCOV Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=["lcov"]),
                        Path("setup.cfg"): ConfigEntry(keys=["coverage:lcov"]),
                        Path("tox.ini"): ConfigEntry(keys=["coverage:lcov"]),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "lcov"]
                        ),
                    },
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
        if is_uv_used():
            box_print(f"Run 'uv run deptry {_dir}' to run deptry.")
        else:
            box_print(f"Run 'deptry {_dir}' to run deptry.")

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return [Dependency(name="deptry")]

    def get_config_spec(self) -> ConfigSpec:
        # https://deptry.com/usage/#configuration
        return ConfigSpec.from_flat(
            file_managers=[PyprojectTOMLManager()],
            resolution="first",
            config_items=[
                ConfigItem(
                    description="Overall config",
                    root={Path("pyproject.toml"): ConfigEntry(keys=["tool", "deptry"])},
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
                name=f"Run {self.name}",
                caches=["uv"],
                script=BitbucketScript(
                    [
                        BitbucketScriptItemAnchor(name="install-uv"),
                        f"uv run deptry {_dir}",
                    ]
                ),
            )
        ]

    def is_managed_rule(self, rule: str) -> bool:
        return rule.startswith("DEP") and rule[3:].isdigit()

    def select_rules(self, rules: list[str]) -> None:
        """Does nothing for deptry - all rules are automatically enabled by default."""

    def get_selected_rules(self) -> list[str]:
        """No notion of selection for deptry.

        This doesn't mean rules won't be enabled, it just means we don't keep track
        of selection for them.
        """
        return []

    def deselect_rules(self, rules: list[str]) -> None:
        """Does nothing for deptry - all rules are automatically enabled by default."""

    def ignore_rules(self, rules: list[str]) -> None:
        rules = sorted(set(rules) - set(self.get_ignored_rules()))

        if not rules:
            return

        rules_str = ", ".join([f"'{rule}'" for rule in rules])
        s = "" if len(rules) == 1 else "s"

        (file_manager,) = self.get_active_config_file_managers()
        _ensure_exists(file_manager)
        tick_print(
            f"Ignoring {self.name} rule{s} {rules_str} in '{file_manager.name}'."
        )
        keys = self._get_ignore_keys(file_manager)
        file_manager.extend_list(keys=keys, values=rules)

    def get_ignored_rules(self) -> list[str]:
        (file_manager,) = self.get_active_config_file_managers()
        keys = self._get_ignore_keys(file_manager)
        try:
            rules: list[str] = file_manager[keys]
        except (KeyError, FileNotFoundError):
            rules = []

        return rules

    def _get_ignore_keys(self, file_manager: KeyValueFileManager) -> list[str]:
        """Get the keys for the ignored rules in the given file manager."""
        if isinstance(file_manager, PyprojectTOMLManager):
            return ["tool", "deptry", "ignore"]
        else:
            msg = (
                f"Unknown location for ignored {self.name} rules for file manager "
                f"'{file_manager.name}' of type {file_manager.__class__.__name__}."
            )
            raise NotImplementedError(msg)


IMPORT_LINTER_CONTRACT_MIN_MODULE_COUNT = 3


class ImportLinterTool(Tool):
    # https://github.com/seddonym/import-linter

    @property
    def name(self) -> str:
        return "Import Linter"

    def print_how_to_use(self) -> None:
        if PreCommitTool().is_used():
            if is_uv_used():
                box_print(
                    f"Run 'uv run pre-commit run lint-imports --all-files' to run {self.name}."
                )
            else:
                box_print(
                    f"Run 'pre-commit run lint-imports --all-files' to run {self.name}."
                )
        elif is_uv_used():
            box_print(f"Run 'uv run lint-imports' to run {self.name}.")
        else:
            box_print(f"Run 'lint-imports' to run {self.name}.")

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        # We need to add the import-linter package itself as a dev dependency.
        # This is because it needs to run from within the virtual environment.
        return [Dependency(name="import-linter")]

    def get_config_spec(self) -> ConfigSpec:
        # https://import-linter.readthedocs.io/en/stable/usage.html

        root_packages = sorted(get_importable_packages())
        if not root_packages:
            # Couldn't find any packages, we're assuming the package name is the name
            # of the project. Warn the user accordingly.
            name = get_project_name()
            warn_print("Could not find any importable packages.")
            warn_print(f"Assuming the package name is {name}.")
            root_packages = [name]

        contracts: list[dict] = []
        for root_package in root_packages:
            try:
                layered_architecture_by_module = get_layered_architectures(root_package)
            except ImportGraphBuildFailedError:
                layered_architecture_by_module = {
                    root_package: LayeredArchitecture(layers=[], excluded=set())
                }

            layered_architecture_by_module = dict(
                sorted(
                    layered_architecture_by_module.items(),
                    key=lambda item: item[0].count("."),
                )
            )

            min_depth = min(
                (module.count(".") for module in layered_architecture_by_module),
                default=0,
            )
            for module, layered_architecture in layered_architecture_by_module.items():
                if (
                    len(contracts) > 0
                    and module.count(".") > min_depth
                    and (
                        layered_architecture.module_count()
                        < IMPORT_LINTER_CONTRACT_MIN_MODULE_COUNT
                    )
                ):
                    # This contract is too small and we already have one. Also, we have
                    # waited until we have finished a complete depth level (e.g. we
                    # have done all of a.b, a.c, and a.d so we won't go on to a.b.e)
                    continue

                layers = []
                for layer in layered_architecture.layers:
                    layers.append(" | ".join(sorted(layer)))

                contract = {
                    "name": f"{module}",
                    "type": "layers",
                    "layers": layers,
                    "containers": [module],
                    "exhaustive": True,
                }

                if layered_architecture.excluded:
                    contract["exhaustive_ignores"] = sorted(
                        layered_architecture.excluded
                    )

                contracts.append(contract)

        if not contracts:
            raise AssertionError

        ini_contracts_config_items = []
        for idx, contract in enumerate(contracts):
            # Cast bools to strings for INI files
            ini_contract = contract.copy()
            ini_contract["exhaustive"] = str(ini_contract["exhaustive"])

            ini_contracts_config_items.append(
                ConfigItem(
                    description=f"Itemized Contract {idx} (INI)",
                    root={
                        Path("setup.cfg"): ConfigEntry(
                            keys=[f"importlinter:contract:{idx}"],
                            value=ini_contract,
                        ),
                        Path(".importlinter"): ConfigEntry(
                            keys=[f"importlinter:contract:{idx}"],
                            value=ini_contract,
                        ),
                    },
                    applies_to_all=False,
                )
            )

        return ConfigSpec(
            file_manager_by_relative_path={
                Path("setup.cfg"): SetupCFGManager(),
                Path(".importlinter"): DotImportLinterManager(),
                Path("pyproject.toml"): PyprojectTOMLManager(),
            },
            resolution="first",
            config_items=[
                ConfigItem(
                    description="Overall config",
                    root={
                        Path("setup.cfg"): ConfigEntry(keys=["importlinter"]),
                        Path(".importlinter"): ConfigEntry(keys=["importlinter"]),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "importlinter"]
                        ),
                    },
                ),
                ConfigItem(
                    description="Root packages",
                    root={
                        Path("setup.cfg"): ConfigEntry(
                            keys=["importlinter", "root_packages"], value=root_packages
                        ),
                        Path(".importlinter"): ConfigEntry(
                            keys=["importlinter", "root_packages"], value=root_packages
                        ),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "importlinter", "root_packages"],
                            value=root_packages,
                        ),
                    },
                ),
                ConfigItem(
                    description="Listed Contracts (TOML)",
                    root={
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "importlinter", "contracts"], value=contracts
                        ),
                    },
                    applies_to_all=False,
                ),
                *ini_contracts_config_items,
            ],
        )

    def get_pre_commit_repos(self) -> list[LocalRepo | UriRepo]:
        return [
            LocalRepo(
                repo="local",
                hooks=[
                    HookDefinition(
                        id="import-linter",
                        name="import-linter",
                        pass_filenames=False,
                        entry="uv run --frozen --offline lint-imports",
                        language=Language("system"),
                        require_serial=True,
                        always_run=True,
                    )
                ],
            )
        ]

    def get_managed_files(self) -> list[Path]:
        return [Path(".importlinter")]

    def get_bitbucket_steps(self) -> list[BitbucketStep]:
        return [
            BitbucketStep(
                name=f"Run {self.name}",
                caches=["uv"],
                script=BitbucketScript(
                    [
                        BitbucketScriptItemAnchor(name="install-uv"),
                        "uv run lint-imports",
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
        if is_uv_used():
            box_print(
                "Run 'uv run pre-commit run --all-files' to run the hooks manually."
            )
        else:
            box_print("Run 'pre-commit run --all-files' to run the hooks manually.")

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return [Dependency(name="pre-commit")]

    def get_managed_files(self) -> list[Path]:
        return [Path(".pre-commit-config.yaml")]

    def get_bitbucket_steps(self) -> list[BitbucketStep]:
        return [
            BitbucketStep(
                name=f"Run {self.name}",
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
            if is_uv_used():
                box_print(
                    f"Run 'uv run pre-commit run pyproject-fmt --all-files' to run {self.name}."
                )
            else:
                box_print(
                    f"Run 'pre-commit run pyproject-fmt --all-files' to run {self.name}."
                )
        elif is_uv_used():
            box_print(f"Run 'uv run pyproject-fmt pyproject.toml' to run {self.name}.")
        else:
            box_print(f"Run 'pyproject-fmt pyproject.toml' to run {self.name}.")

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return [Dependency(name="pyproject-fmt")]

    def get_config_spec(self) -> ConfigSpec:
        # https://pyproject-fmt.readthedocs.io/en/latest/#configuration-via-file
        return ConfigSpec.from_flat(
            file_managers=[PyprojectTOMLManager()],
            resolution="first",
            config_items=[
                ConfigItem(
                    description="Overall Config",
                    root={
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "pyproject-fmt"]
                        )
                    },
                ),
                ConfigItem(
                    description="Keep Full Version",
                    root={
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "pyproject-fmt", "keep_full_version"],
                            get_value=lambda: True,
                        )
                    },
                ),
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
                name=f"Run {self.name}",
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

    def remove_managed_files(self) -> None:
        # https://github.com/nathanjmcdougall/usethis-python/issues/416
        # We need to step through the tools and see if pyproject.toml is the active
        # config file.
        # If it isn't an active config file, no action is required.
        # If it is an active config file, we  display a message to the user to inform
        # them that the active config is being removed and they need to re-configure
        # the tool

        box_print("Check that important config in 'pyproject.toml' is not lost.")

        for tool in ALL_TOOLS:
            if (
                tool.is_used()
                and PyprojectTOMLManager() in tool.get_active_config_file_managers()
            ):
                # Warn the user
                box_print(
                    f"The {tool.name} tool was using 'pyproject.toml' for config, "
                    f"but that file is being removed. You will need to re-configure it."
                )

        super().remove_managed_files()


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
        if is_uv_used():
            box_print("Run 'uv run pytest' to run the tests.")
        else:
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
        value_ini = value.copy()
        # https://docs.pytest.org/en/stable/reference/reference.html#confval-xfail_strict
        value_ini["xfail_strict"] = "True"  # stringify boolean

        return ConfigSpec.from_flat(
            file_managers=[
                PytestINIManager(),
                DotPytestINIManager(),
                PyprojectTOMLManager(),
                ToxINIManager(),
                SetupCFGManager(),
            ],
            resolution="bespoke",
            config_items=[
                ConfigItem(
                    description="Overall Config",
                    root={
                        Path("pytest.ini"): ConfigEntry(keys=[]),
                        Path(".pytest.ini"): ConfigEntry(keys=[]),
                        Path("pyproject.toml"): ConfigEntry(keys=["tool", "pytest"]),
                        Path("tox.ini"): ConfigEntry(keys=["pytest"]),
                        Path("setup.cfg"): ConfigEntry(keys=["tool:pytest"]),
                    },
                ),
                ConfigItem(
                    description="INI-Style Options",
                    root={
                        Path("pytest.ini"): ConfigEntry(
                            keys=["pytest"], get_value=lambda: value_ini
                        ),
                        Path(".pytest.ini"): ConfigEntry(
                            keys=["pytest"], get_value=lambda: value_ini
                        ),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "pytest", "ini_options"],
                            get_value=lambda: value,
                        ),
                        Path("tox.ini"): ConfigEntry(
                            keys=["pytest"], get_value=lambda: value_ini
                        ),
                        Path("setup.cfg"): ConfigEntry(
                            keys=["tool:pytest"], get_value=lambda: value_ini
                        ),
                    },
                ),
            ],
        )

    def get_managed_files(self) -> list[Path]:
        return [Path(".pytest.ini"), Path("pytest.ini"), Path("tests/conftest.py")]

    def get_associated_ruff_rules(self) -> list[str]:
        return ["PT"]

    def get_active_config_file_managers(self) -> set[KeyValueFileManager]:
        # This is a variant of the "first" method
        config_spec = self.get_config_spec()
        assert config_spec.resolution == "bespoke"
        # As per https://docs.pytest.org/en/stable/reference/customize.html#finding-the-rootdir
        # Files will only be matched for configuration if:
        # - pytest.ini: will always match and take precedence, even if empty.
        # - pyproject.toml: contains a [tool.pytest.ini_options] table.
        # - tox.ini: contains a [pytest] section.
        # - setup.cfg: contains a [tool:pytest] section.
        # Finally, a pyproject.toml file will be considered the configfile if no other
        # match was found, in this case even if it does not contain a
        # [tool.pytest.ini_options] table
        # Also, the docs mention that the hidden .pytest.ini variant is allowed, in my
        # experimentation is takes precedence over pyproject.toml but not pytest.ini.

        for (
            relative_path,
            file_manager,
        ) in config_spec.file_manager_by_relative_path.items():
            path = Path.cwd() / relative_path
            if path.exists() and path.is_file():
                if isinstance(file_manager, PyprojectTOMLManager):
                    if ["tool", "pytest", "ini_options"] in file_manager:
                        return {file_manager}
                    else:
                        continue
                return {file_manager}

        # Second chance for pyproject.toml
        for (
            relative_path,
            file_manager,
        ) in config_spec.file_manager_by_relative_path.items():
            path = Path.cwd() / relative_path
            if (
                path.exists()
                and path.is_file()
                and isinstance(file_manager, PyprojectTOMLManager)
            ):
                return {file_manager}

        file_managers = config_spec.file_manager_by_relative_path.values()
        if not file_managers:
            return set()

        # Use the preferred default file since there's no existing file.
        preferred_file_manager = self.preferred_file_manager()
        if preferred_file_manager not in file_managers:
            msg = (
                f"The preferred file manager '{preferred_file_manager}' is not "
                f"among the file managers '{file_managers}' for the tool "
                f"'{self.name}'"
            )
            raise NotImplementedError(msg)
        return {preferred_file_manager}

    def get_bitbucket_steps(self) -> list[BitbucketStep]:
        versions = get_supported_major_python_versions()

        steps = []
        for version in versions:
            steps.append(
                BitbucketStep(
                    name=f"Test on 3.{version}",
                    caches=["uv"],
                    script=BitbucketScript(
                        [
                            BitbucketScriptItemAnchor(name="install-uv"),
                            f"uv run --python 3.{version} pytest -x --junitxml=test-reports/report.xml",
                        ]
                    ),
                )
            )
        return steps

    def get_managed_bitbucket_step_names(self) -> list[str]:
        names = set()
        for step in get_steps_in_default():
            if step.name is not None:
                match = re.match(r"^Test on 3\.\d+$", step.name)
                if match:
                    names.add(step.name)

        for step in self.get_bitbucket_steps():
            if step.name is not None:
                names.add(step.name)

        return sorted(names)


class RequirementsTxtTool(Tool):
    # https://pip.pypa.io/en/stable/reference/requirements-file-format/

    @property
    def name(self) -> str:
        return "requirements.txt"

    def print_how_to_use(self) -> None:
        if PreCommitTool().is_used():
            if is_uv_used():
                box_print(
                    "Run 'uv run pre-commit run uv-export' to write 'requirements.txt'."
                )
            else:
                box_print("Run 'pre-commit run uv-export' to write 'requirements.txt'.")
        else:
            if not is_uv_used():
                # This is a very crude approach as a temporary measure.
                box_print("Install uv to use 'uv export'.")

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
        if is_uv_used():
            box_print(
                "Run 'uv run ruff check --fix' to run the Ruff linter with autofixes."
            )
            box_print("Run 'uv run ruff format' to run the Ruff formatter.")
        else:
            box_print("Run 'ruff check --fix' to run the Ruff linter with autofixes.")
            box_print("Run 'ruff format' to run the Ruff formatter.")

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return [Dependency(name="ruff")]

    def get_config_spec(self) -> ConfigSpec:
        # https://docs.astral.sh/ruff/configuration/#config-file-discovery

        line_length = 88

        return ConfigSpec.from_flat(
            file_managers=[
                DotRuffTOMLManager(),
                RuffTOMLManager(),
                PyprojectTOMLManager(),
            ],
            resolution="first",
            config_items=[
                ConfigItem(
                    description="Overall config",
                    root={
                        Path(".ruff.toml"): ConfigEntry(keys=[]),
                        Path("ruff.toml"): ConfigEntry(keys=[]),
                        Path("pyproject.toml"): ConfigEntry(keys=["tool", "ruff"]),
                    },
                ),
                ConfigItem(
                    description="Line length",
                    root={
                        Path(".ruff.toml"): ConfigEntry(
                            keys=["line-length"], get_value=lambda: line_length
                        ),
                        Path("ruff.toml"): ConfigEntry(
                            keys=["line-length"], get_value=lambda: line_length
                        ),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "ruff", "line-length"],
                            get_value=lambda: line_length,
                        ),
                    },
                ),
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
                name=f"Run {self.name}",
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

    def select_rules(self, rules: list[str]) -> None:
        """Add Ruff rules to the project."""
        rules = sorted(set(rules) - set(self.get_selected_rules()))

        if not rules:
            return

        rules_str = ", ".join([f"'{rule}'" for rule in rules])
        s = "" if len(rules) == 1 else "s"

        (file_manager,) = self.get_active_config_file_managers()
        _ensure_exists(file_manager)
        tick_print(
            f"Enabling {self.name} rule{s} {rules_str} in '{file_manager.name}'."
        )
        keys = self._get_select_keys(file_manager)
        file_manager.extend_list(keys=keys, values=rules)

    def ignore_rules(self, rules: list[str]) -> None:
        """Ignore Ruff rules in the project."""
        rules = sorted(set(rules) - set(self.get_ignored_rules()))

        if not rules:
            return

        rules_str = ", ".join([f"'{rule}'" for rule in rules])
        s = "" if len(rules) == 1 else "s"

        (file_manager,) = self.get_active_config_file_managers()
        _ensure_exists(file_manager)
        tick_print(
            f"Ignoring {self.name} rule{s} {rules_str} in '{file_manager.name}'."
        )
        keys = self._get_ignore_keys(file_manager)
        file_manager.extend_list(keys=keys, values=rules)

    def deselect_rules(self, rules: list[str]) -> None:
        """Ensure Ruff rules are not selected in the project."""
        rules = list(set(rules) & set(self.get_selected_rules()))

        if not rules:
            return

        rules_str = ", ".join([f"'{rule}'" for rule in rules])
        s = "" if len(rules) == 1 else "s"

        (file_manager,) = self.get_active_config_file_managers()
        _ensure_exists(file_manager)
        tick_print(
            f"Disabling {self.name} rule{s} {rules_str} in '{file_manager.name}'."
        )
        keys = self._get_select_keys(file_manager)
        file_manager.remove_from_list(keys=keys, values=rules)

    def get_selected_rules(self) -> list[str]:
        """Get the Ruff rules selected in the project."""
        (file_manager,) = self.get_active_config_file_managers()

        keys = self._get_select_keys(file_manager)
        try:
            rules: list[str] = file_manager[keys]
        except (KeyError, FileNotFoundError):
            rules = []

        return rules

    def get_ignored_rules(self) -> list[str]:
        """Get the Ruff rules ignored in the project."""
        (file_manager,) = self.get_active_config_file_managers()
        keys = self._get_ignore_keys(file_manager)
        try:
            rules: list[str] = file_manager[keys]
        except (KeyError, FileNotFoundError):
            rules = []

        return rules

    def set_docstyle(self, style: Literal["numpy", "google", "pep257"]) -> None:
        (file_manager,) = self.get_active_config_file_managers()

        keys = self._get_docstyle_keys(file_manager)
        if keys in file_manager and file_manager[keys] == style:
            # Already set properly
            return

        msg = f"Setting docstring style to '{style}' in '{file_manager.name}'."
        tick_print(msg)
        file_manager[self._get_docstyle_keys(file_manager)] = style

    def get_docstyle(self) -> Literal["numpy", "google", "pep257"] | None:
        """Get the docstring style set in the project."""
        (file_manager,) = self.get_active_config_file_managers()
        keys = self._get_docstyle_keys(file_manager)
        try:
            docstyle = file_manager[keys]
        except (KeyError, FileNotFoundError):
            docstyle = None

        if docstyle not in ("numpy", "google", "pep257"):
            # Docstyle is not set or is invalid
            return None

        return docstyle

    def _are_pydocstyle_rules_selected(self) -> bool:
        """Check if pydocstyle rules are selected in the configuration."""
        # If "ALL" is selected, or any rule whose alphabetical part is "D".
        rules = self.get_selected_rules()
        for rule in rules:
            if rule == "ALL":
                return True
            if self._is_pydocstyle_rule(rule):
                return True
        return False

    @staticmethod
    def _is_pydocstyle_rule(rule: str) -> bool:
        return [d for d in rule if d.isalpha()] == ["D"]

    def _get_select_keys(self, file_manager: KeyValueFileManager) -> list[str]:
        """Get the keys for the select rules in the given file manager."""
        if isinstance(file_manager, PyprojectTOMLManager):
            return ["tool", "ruff", "lint", "select"]
        elif isinstance(file_manager, RuffTOMLManager | DotRuffTOMLManager):
            return ["lint", "select"]
        else:
            msg = (
                f"Unknown location for selected {self.name} rules for file manager "
                f"'{file_manager.name}' of type {file_manager.__class__.__name__}."
            )
            raise NotImplementedError(msg)

    def _get_ignore_keys(self, file_manager: KeyValueFileManager) -> list[str]:
        """Get the keys for the ignored rules in the given file manager."""
        if isinstance(file_manager, PyprojectTOMLManager):
            return ["tool", "ruff", "lint", "ignore"]
        elif isinstance(file_manager, RuffTOMLManager | DotRuffTOMLManager):
            return ["lint", "ignore"]
        else:
            msg = (
                f"Unknown location for ignored {self.name} rules for file manager "
                f"'{file_manager.name}' of type {file_manager.__class__.__name__}."
            )
            raise NotImplementedError(msg)

    def _get_docstyle_keys(self, file_manager: KeyValueFileManager) -> list[str]:
        """Get the keys for the docstyle rules in the given file manager."""
        if isinstance(file_manager, PyprojectTOMLManager):
            return ["tool", "ruff", "lint", "pydocstyle", "convention"]
        elif isinstance(file_manager, RuffTOMLManager | DotRuffTOMLManager):
            return ["lint", "pydocstyle", "convention"]
        else:
            msg = (
                f"Unknown location for {self.name} docstring style for file manager "
                f"'{file_manager.name}' of type {file_manager.__class__.__name__}."
            )
            raise NotImplementedError(msg)


def _ensure_exists(file_manager: KeyValueFileManager) -> None:
    """Ensure the file manager exists."""
    if isinstance(file_manager, PyprojectTOMLManager):
        ensure_pyproject_toml()
    elif not file_manager.path.exists():
        # Create the file if it doesn't exist. By assumption, an empty file is valid.
        file_manager.path.touch()


ALL_TOOLS: list[Tool] = [
    CodespellTool(),
    CoverageTool(),
    DeptryTool(),
    ImportLinterTool(),
    PreCommitTool(),
    PyprojectFmtTool(),
    PyprojectTOMLTool(),
    PytestTool(),
    RequirementsTxtTool(),
    RuffTool(),
]
