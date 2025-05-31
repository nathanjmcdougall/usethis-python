from __future__ import annotations

from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from typing_extensions import assert_never

from usethis._console import tick_print
from usethis._integrations.ci.bitbucket.steps import (
    add_bitbucket_step_in_default,
    bitbucket_steps_are_equivalent,
    get_steps_in_default,
    remove_bitbucket_step_from_default,
)
from usethis._integrations.ci.bitbucket.used import is_bitbucket_used
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.pre_commit.hooks import (
    add_repo,
    get_hook_ids,
    hook_ids_are_equivalent,
    remove_hook,
)
from usethis._integrations.uv.deps import (
    add_deps_to_group,
    is_dep_in_any_group,
    remove_deps_from_group,
)
from usethis._tool.config import ConfigSpec, NoConfigValue
from usethis._tool.rule import RuleConfig

if TYPE_CHECKING:
    from usethis._integrations.ci.bitbucket.schema import Step as BitbucketStep
    from usethis._integrations.pre_commit.schema import LocalRepo, UriRepo
    from usethis._integrations.uv.deps import (
        Dependency,
    )
    from usethis._io import KeyValueFileManager
    from usethis._tool.config import ResolutionT
    from usethis._tool.rule import Rule


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
        return self.is_config_present()

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
                    hook_ids_are_equivalent(hook.id, hook_id)
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
        return self._get_active_config_file_managers_from_resolution(
            resolution,
            file_manager_by_relative_path=config_spec.file_manager_by_relative_path,
        )

    def _get_active_config_file_managers_from_resolution(
        self,
        resolution: ResolutionT,
        *,
        file_manager_by_relative_path: dict[Path, KeyValueFileManager],
    ) -> set[KeyValueFileManager]:
        if resolution == "first":
            # N.B. keep this roughly in sync with the bespoke logic for pytest
            # since that logic is based on this logic.
            for (
                relative_path,
                file_manager,
            ) in file_manager_by_relative_path.items():
                path = Path.cwd() / relative_path
                if path.exists() and path.is_file():
                    return {file_manager}
        elif resolution == "first_content":
            config_spec = self.get_config_spec()
            for relative_path, file_manager in file_manager_by_relative_path.items():
                path = Path.cwd() / relative_path
                if path.exists() and path.is_file():
                    # We check whether any of the managed config exists
                    for config_item in config_spec.config_items:
                        if config_item.root[relative_path].keys in file_manager:
                            return {file_manager}
        elif resolution == "bespoke":
            msg = (
                "The bespoke resolution method is not yet implemented for the tool "
                f"{self.name}."
            )
            raise NotImplementedError(msg)
        else:
            assert_never(resolution)

        file_managers = file_manager_by_relative_path.values()
        if not file_managers:
            return set()

        preferred_file_manager = self.preferred_file_manager()
        if preferred_file_manager not in file_managers:
            msg = (
                f"The preferred file manager '{preferred_file_manager}' is not "
                f"among the file managers '{file_managers}' for the tool "
                f"'{self.name}'"
            )
            raise NotImplementedError(msg)
        return {preferred_file_manager}

    def preferred_file_manager(self) -> KeyValueFileManager:
        """If there is no currently active config file, this is the preferred one."""
        return PyprojectTOMLManager()

    def is_config_present(self) -> bool:
        """Whether any of the tool's managed config sections are present."""
        return self._is_config_spec_present(self.get_config_spec())

    def _is_config_spec_present(self, config_spec: ConfigSpec) -> bool:
        """Check whether a bespoke config spec is present.

        The reason for splitting this method out from the overall `is_config_present`
        method is to allow for checking a `config_spec` different from the main
        config_spec (e.g. a subset of it to distinguish between two different aspects
        of a tool, e.g. Ruff's linter vs. formatter configuration sections).
        """
        for config_item in config_spec.config_items:
            if not config_item.managed:
                continue

            for relative_path, entry in config_item.root.items():
                file_manager = config_spec.file_manager_by_relative_path[relative_path]
                if not (file_manager.path.exists() and file_manager.path.is_file()):
                    continue

                if file_manager.__contains__(entry.keys):
                    return True

        return False

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

            if isinstance(entry.get_value(), NoConfigValue):
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
        config_spec = self.get_config_spec()

        first_removal = True
        for config_item in config_spec.config_items:
            if not config_item.managed:
                continue

            for (
                relative_path,
                file_manager,
            ) in config_spec.file_manager_by_relative_path.items():
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
                bitbucket_steps_are_equivalent(step, step_)
                for step_ in self.get_bitbucket_steps()
            ):
                remove_bitbucket_step_from_default(step)

    def get_rule_config(self) -> RuleConfig:
        """Get the linter rule configuration associated with this tool."""
        return RuleConfig()

    def is_managed_rule(self, rule: Rule) -> bool:
        """Determine if a rule is managed by this tool."""
        return False

    def select_rules(self, rules: list[Rule]) -> None:
        """Select the rules managed by the tool.

        These rules are not validated; it is assumed they are valid rules for the tool,
        and that the tool will be able to manage them.
        """

    def get_selected_rules(self) -> list[Rule]:
        """Get the rules managed by the tool that are currently selected."""
        return []

    def ignore_rules(self, rules: list[Rule]) -> None:
        """Ignore rules managed by the tool.

        Ignoring a rule is different from deselecting it - it means that even if it
        selected, it will not take effect. See the way that Ruff configuration works to
        understand this concept in more detail.

        These rules are not validated; it is assumed they are valid rules for the tool,
        and that the tool will be able to manage them.
        """

    def unignore_rules(self, rules: list[str]) -> None:
        """Stop ignoring rules managed by the tool.

        These rules are not validated; it is assumed they are valid rules for the tool,
        and that the tool will be able to manage them.
        """

    def get_ignored_rules(self) -> list[Rule]:
        """Get the ignored rules managed by the tool."""
        return []

    def deselect_rules(self, rules: list[Rule]) -> None:
        """Deselect the rules managed by the tool.

        Any rules that aren't already selected are ignored.
        """
