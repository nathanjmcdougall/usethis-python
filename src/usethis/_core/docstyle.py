from __future__ import annotations

from typing import TYPE_CHECKING

from usethis._core.tool import use_ruff
from usethis._tool.impl.ruff import RuffTool

if TYPE_CHECKING:
    from usethis._types.docstyle import DocStyleEnum


def use_docstyle(style: DocStyleEnum) -> None:
    if not RuffTool().is_used():
        use_ruff(minimal=True)

    RuffTool().set_docstyle(style.value)

    if not RuffTool()._are_pydocstyle_rules_selected():
        RuffTool().select_rules(["D2", "D3", "D4"])
