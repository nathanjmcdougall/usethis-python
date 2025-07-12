from __future__ import annotations

from typing import TypeAlias

from usethis._tool.impl.codespell import CodespellTool
from usethis._tool.impl.coverage_py import CoveragePyTool
from usethis._tool.impl.deptry import DeptryTool
from usethis._tool.impl.import_linter import ImportLinterTool
from usethis._tool.impl.mkdocs import MkDocsTool
from usethis._tool.impl.pre_commit import PreCommitTool
from usethis._tool.impl.pyproject_fmt import PyprojectFmtTool
from usethis._tool.impl.pyproject_toml import PyprojectTOMLTool
from usethis._tool.impl.pytest import PytestTool
from usethis._tool.impl.requirements_txt import RequirementsTxtTool
from usethis._tool.impl.ruff import RuffTool

SupportedToolType: TypeAlias = (
    CodespellTool
    | CoveragePyTool
    | DeptryTool
    | ImportLinterTool
    | MkDocsTool
    | PreCommitTool
    | PyprojectFmtTool
    | PyprojectTOMLTool
    | PytestTool
    | RequirementsTxtTool
    | RuffTool
)

ALL_TOOLS: list[SupportedToolType] = [
    CodespellTool(),
    CoveragePyTool(),
    DeptryTool(),
    ImportLinterTool(),
    MkDocsTool(),
    PreCommitTool(),
    PyprojectFmtTool(),
    PyprojectTOMLTool(),
    PytestTool(),
    RequirementsTxtTool(),
    RuffTool(),
]
