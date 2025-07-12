from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

from pydantic import BaseModel, InstanceOf

from usethis._config import usethis_config
from usethis._integrations.backend.uv.init import ensure_pyproject_toml
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._io import Key, KeyValueFileManager

if TYPE_CHECKING:
    from typing_extensions import Self

    from usethis._io import UsethisFileManager

ResolutionT: TypeAlias = Literal["first", "first_content", "bespoke"]


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
                      found, the preferred file manager is used.
                    - "first_content": Using the order in file_managers, the first file
                      to contain managed configuration (as per config_items) is used.
                      All subsequent files are ignored. If no files are found with any
                      managed config, the found, the preferred file manager is used.
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


class NoConfigValue:
    pass


def _get_no_config_value() -> NoConfigValue:
    return NoConfigValue()


class ConfigEntry(BaseModel):
    """A configuration entry in a config file associated with a tool.

    Attributes:
        keys: A sequentially nested sequence of keys giving a single configuration item.
        value: The default value to be placed at the under the key sequence. By default,
               no configuration will be added, which is most appropriate for top-level
               configuration sections like [tool.usethis] under which the entire tool's
               config gets placed.

    """

    keys: list[Key]
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
        return {(usethis_config.cpd() / path).resolve() for path in self.root}


def ensure_file_manager_exists(file_manager: UsethisFileManager) -> None:
    """Ensure the file manager exists."""
    if isinstance(file_manager, PyprojectTOMLManager):
        ensure_pyproject_toml()
    elif not file_manager.path.exists():
        # Create the file if it doesn't exist. By assumption, an empty file is valid.
        file_manager.path.touch()
