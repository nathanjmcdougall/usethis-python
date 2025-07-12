from __future__ import annotations

from typing import TYPE_CHECKING

from usethis._config import usethis_config
from usethis._integrations.backend.uv.call import call_uv_subprocess
from usethis._integrations.backend.uv.errors import (
    UVDepGroupError,
    UVSubprocessFailedError,
)
from usethis._integrations.backend.uv.toml import UVTOMLManager
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager

if TYPE_CHECKING:
    from usethis._types.deps import Dependency


def add_dep_to_group_via_uv(dep: Dependency, group: str):
    try:
        call_uv_subprocess(
            ["add", "--group", group, str(dep)],
            change_toml=True,
        )
    except UVSubprocessFailedError as err:
        msg = f"Failed to add '{dep}' to the '{group}' dependency group:\n{err}"
        msg += (usethis_config.cpd() / "pyproject.toml").read_text()
        raise UVDepGroupError(msg) from None


def remove_dep_from_group_via_uv(dep: Dependency, group: str):
    try:
        call_uv_subprocess(["remove", "--group", group, str(dep)], change_toml=True)
    except UVSubprocessFailedError as err:
        msg = f"Failed to remove '{dep}' from the '{group}' dependency group:\n{err}"
        raise UVDepGroupError(msg) from None


def get_default_groups_via_uv() -> list[str]:
    """Get the default dependency groups from the uv configuration."""
    try:
        if UVTOMLManager().path.exists():
            default_groups = UVTOMLManager()[["default-groups"]]
        else:
            default_groups = PyprojectTOMLManager()[["tool", "uv", "default-groups"]]
        if not isinstance(default_groups, list):
            default_groups = []
    except KeyError:
        default_groups = []

    return default_groups
