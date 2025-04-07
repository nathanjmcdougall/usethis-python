from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel

from usethis._console import tick_print, warn_print
from usethis._core.readme import add_readme, get_readme_path
from usethis._integrations.project.name import get_project_name

if TYPE_CHECKING:
    from typing_extensions import Self


class Badge(BaseModel):
    markdown: str

    @property
    def name(self) -> str | None:
        match = re.match(r"^\s*\[!\[(.*)\]\(.*\)\]\(.*\)\s*$", self.markdown)
        if match:
            return match.group(1)
        match = re.match(r"^\s*\!\[(.*)\]\(.*\)\s*$", self.markdown)
        if match:
            return match.group(1)
        return None

    def equivalent_to(self, other: Self) -> bool:
        return self.name == other.name


def get_pre_commit_badge() -> Badge:
    return Badge(
        markdown="[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)"
    )


def get_pypi_badge() -> Badge:
    name = get_project_name()
    return Badge(
        markdown=f"[![PyPI Version](https://img.shields.io/pypi/v/{name}.svg)](<https://pypi.python.org/pypi/{name})"
    )


def get_ruff_badge() -> Badge:
    return Badge(
        markdown="[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)"
    )


def get_uv_badge() -> Badge:
    return Badge(
        markdown="[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)"
    )


def get_usethis_badge() -> Badge:
    return Badge(
        markdown="[![usethis](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/nathanjmcdougall/usethis-python/main/assets/badge/v1.json)](https://github.com/nathanjmcdougall/usethis-python)"
    )


def get_badge_order() -> list[Badge]:
    return [
        get_pypi_badge(),
        get_uv_badge(),
        get_ruff_badge(),
        get_pre_commit_badge(),
        get_usethis_badge(),
    ]


@dataclass
class MarkdownH1Status:
    """A way of keeping track of whether we're in a block of H1 tags.

    We don't want to add badges inside a block of H1 tags.
    """

    h1_count: int = 0
    in_block: bool = False

    def update_from_line(self, line: str) -> None:
        self.h1_count += self._count_h1_open_tags(line)
        self.in_block = self.h1_count > 0
        self.h1_count -= self._count_h1_close_tags(line)

    @staticmethod
    def _count_h1_open_tags(line: str) -> int:
        h1_start_match = re.match(r"(<h1\s.*>)", line)
        if h1_start_match is not None:
            return len(h1_start_match.groups())
        return 0

    @staticmethod
    def _count_h1_close_tags(line: str) -> int:
        return line.count("</h1>")


def add_badge(badge: Badge) -> None:
    add_readme()

    try:
        path = _get_markdown_readme_path()
    except FileNotFoundError:
        warn_print("README file not found, printing badge markdown instead...")
        print(badge.markdown)
        return

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        warn_print(
            "README file uses an unsupported encoding, printing badge markdown instead..."
        )
        print(badge.markdown)
        return

    original_lines = content.splitlines()

    prerequisites = _get_prerequisites(badge)

    have_added = False
    have_encountered_badge = False
    h1_status = MarkdownH1Status()
    lines: list[str] = []
    for original_line in original_lines:
        if is_badge(original_line):
            have_encountered_badge = True

        h1_status.update_from_line(original_line)

        original_badge = Badge(markdown=original_line)

        if original_badge.equivalent_to(badge):
            # If the badge is already there, we don't need to do anything
            return

        original_line_is_prerequisite = any(
            original_badge.equivalent_to(prerequisite) for prerequisite in prerequisites
        )
        if not have_added and (
            not original_line_is_prerequisite
            and (not is_blank(original_line) or have_encountered_badge)
            and not is_header(original_line)
            and not h1_status.in_block
        ):
            lines.append(badge.markdown)
            have_added = True

            # Protect the badge we've just added
            if not is_blank(original_line) and not is_badge(original_line):
                lines.append("")

        lines.append(original_line)

    # In case the badge needs to go at the bottom of the file
    if not have_added:
        # Add a blank line between headers and the badge
        if original_lines and is_header(original_lines[-1]):
            lines.append("")
        lines.append(badge.markdown)
        have_added = True

    tick_print(f"Adding {badge.name} badge to 'README.md'.")

    # If the first line is blank, we basically just want to replace it.
    if is_blank(lines[0]):
        del lines[0]

    output = "\n".join(lines)

    # Ensure final newline
    if have_added:
        output = _ensure_final_newline(output)

    path.write_text(output, encoding="utf-8")


def _get_prerequisites(badge: Badge) -> list[Badge]:
    """Get the prerequisites for a badge.

    We want to place the badges in a specific order, so we need to check if we've got
    past those prerequisites.
    """
    prerequisites: list[Badge] = []
    for _b in get_badge_order():
        if badge.equivalent_to(_b):
            break
        prerequisites.append(_b)
    return prerequisites


def _get_markdown_readme_path() -> Path:
    path = get_readme_path()

    if path.name == "README.md":
        pass
    elif path.name == "README":
        warn_print("Assuming 'README' file is Markdown.")
    else:
        msg = f"README file '{path.name}' is not Markdown based on its extension."
        raise FileNotFoundError(msg)

    return path


def _ensure_final_newline(content: str) -> str:
    if not content or content[-1] != "\n":
        content += "\n"
    return content


def is_blank(line: str) -> bool:
    return line.isspace() or not line


def is_header(line: str) -> bool:
    return line.strip().startswith("#")


def is_badge(line: str) -> bool:
    # A heuristic
    return (
        re.match(r"^\[!\[.*\]\(.*\)\]\(.*\)$", line) is not None
        or re.match(r"^\!\[.*\]\(.*\)$", line) is not None
    )


def remove_badge(badge: Badge) -> None:
    path = Path.cwd() / "README.md"

    try:
        path = _get_markdown_readme_path()
    except FileNotFoundError:
        # If there's no README.md, there's nothing to remove
        return

    content = path.read_text(encoding="utf-8")

    original_lines = content.splitlines()
    if content.endswith("\n"):
        original_lines.append("")

    lines: list[str] = []
    have_removed = False
    skip_blank = False
    for idx, original_line in enumerate(original_lines):
        if not skip_blank:
            if Badge(markdown=original_line).equivalent_to(badge):
                tick_print(f"Removing {badge.name} badge from 'README.md'.")
                have_removed = True

                # Merge consecutive blank lines around the badges,
                # if there is only one left
                if (
                    idx - 1 >= 0
                    and idx + 1 < len(original_lines)
                    and is_blank(original_lines[idx - 1])
                    and is_blank(original_lines[idx + 1])
                ):
                    skip_blank = True  # i.e. next iteration once we hit a blank

                continue

            lines.append(original_line)
        else:
            skip_blank = False

    output = "\n".join(lines)

    # Ensure final newline
    if have_removed:
        output = _ensure_final_newline(output)

    path.write_text(output, encoding="utf-8")
