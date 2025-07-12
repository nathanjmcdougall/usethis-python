from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from usethis._config_file import MkDocsYMLManager
from usethis._console import box_print
from usethis._integrations.uv.deps import Dependency
from usethis._integrations.uv.used import is_uv_used
from usethis._tool.base import Tool

if TYPE_CHECKING:
    from usethis._io import KeyValueFileManager
    from usethis._tool.config import ConfigSpec


class MkDocsTool(Tool):
    # https://www.mkdocs.org/

    @property
    def name(self) -> str:
        return "MkDocs"

    def print_how_to_use(self) -> None:
        if is_uv_used():
            box_print("Run 'uv run mkdocs build' to build the documentation.")
            box_print("Run 'uv run mkdocs serve' to serve the documentation locally.")
        else:
            box_print("Run 'mkdocs build' to build the documentation.")
            box_print("Run 'mkdocs serve' to serve the documentation locally.")

    def get_doc_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        deps = [Dependency(name="mkdocs")]

        if unconditional:
            deps.append(Dependency(name="mkdocs-material"))

        return deps

    def get_config_spec(self) -> ConfigSpec:
        """Get the configuration specification for this tool.

        This includes the file managers and resolution methodology.
        """
        # This should be changed to include basic config
        return super().get_config_spec()

    def get_managed_files(self) -> list[Path]:
        """Get (relative) paths to files managed by (solely) this tool."""
        return [Path("mkdocs.yml")]

    def preferred_file_manager(self) -> KeyValueFileManager:
        """If there is no currently active config file, this is the preferred one."""
        # Should set the the mkdocs.yml file manager as the preferred one
        return MkDocsYMLManager()
