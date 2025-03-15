from __future__ import annotations

from usethis._console import tick_print
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager


def select_ruff_rules(rules: list[str]) -> None:
    """Add Ruff rules to the project."""
    rules = sorted(set(rules) - set(get_ruff_rules()))

    if not rules:
        return

    rules_str = ", ".join([f"'{rule}'" for rule in rules])
    s = "" if len(rules) == 1 else "s"
    tick_print(f"Enabling Ruff rule{s} {rules_str} in 'pyproject.toml'.")

    PyprojectTOMLManager().extend_list(
        keys=["tool", "ruff", "lint", "select"], values=rules
    )


def ignore_ruff_rules(rules: list[str]) -> None:
    """Ignore Ruff rules in the project."""
    rules = sorted(set(rules) - set(get_ignored_ruff_rules()))

    if not rules:
        return

    rules_str = ", ".join([f"'{rule}'" for rule in rules])
    s = "" if len(rules) == 1 else "s"
    tick_print(f"Ignoring Ruff rule{s} {rules_str} in 'pyproject.toml'.")

    PyprojectTOMLManager().extend_list(
        keys=["tool", "ruff", "lint", "ignore"], values=rules
    )


def deselect_ruff_rules(rules: list[str]) -> None:
    """Ensure Ruff rules are not selected in the project."""
    rules = list(set(rules) & set(get_ruff_rules()))

    if not rules:
        return

    rules_str = ", ".join([f"'{rule}'" for rule in rules])
    s = "" if len(rules) == 1 else "s"
    tick_print(f"Disabling Ruff rule{s} {rules_str} in 'pyproject.toml'.")

    PyprojectTOMLManager().remove_from_list(
        keys=["tool", "ruff", "lint", "select"], values=rules
    )


def get_ruff_rules() -> list[str]:
    """Get the Ruff rules selected in the project."""
    try:
        rules: list[str] = PyprojectTOMLManager()[["tool", "ruff", "lint", "select"]]
    except KeyError:
        rules = []

    return rules


def get_ignored_ruff_rules() -> list[str]:
    """Get the Ruff rules ignored in the project."""
    try:
        rules: list[str] = PyprojectTOMLManager()[["tool", "ruff", "lint", "ignore"]]
    except KeyError:
        rules = []

    return rules
