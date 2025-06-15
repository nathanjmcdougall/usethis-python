from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from usethis._console import box_print, info_print
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._tool.base import Tool
from usethis._tool.impl.codespell import CodespellTool
from usethis._tool.impl.coverage_py import CoveragePyTool
from usethis._tool.impl.deptry import DeptryTool
from usethis._tool.impl.import_linter import ImportLinterTool
from usethis._tool.impl.pre_commit import PreCommitTool
from usethis._tool.impl.pyproject_fmt import PyprojectFmtTool
from usethis._tool.impl.pytest import PytestTool
from usethis._tool.impl.requirements_txt import RequirementsTxtTool
from usethis._tool.impl.ruff import RuffTool

if TYPE_CHECKING:
    from usethis._integrations.uv.deps import (
        Dependency,
    )

OTHER_TOOLS: list[Tool] = [
    CodespellTool(),
    CoveragePyTool(),
    DeptryTool(),
    ImportLinterTool(),
    PreCommitTool(),
    PyprojectFmtTool(),
    PytestTool(),
    RequirementsTxtTool(),
    RuffTool(),
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
        # https://github.com/usethis-python/usethis-python/issues/416
        # We need to step through the tools and see if pyproject.toml is the active
        # config file.
        # If it isn't an active config file, no action is required.
        # If it is an active config file, we  display a message to the user to inform
        # them that the active config is being removed and they need to re-configure
        # the tool

        box_print("Check that important config in 'pyproject.toml' is not lost.")

        for tool in OTHER_TOOLS:
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
