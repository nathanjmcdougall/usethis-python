from pathlib import Path

from usethis._console import tick_print
from usethis._integrations.pyproject.io_ import pyproject_toml_io_manager


def remove_pyproject_toml() -> None:
    path = Path.cwd() / "pyproject.toml"
    if path.exists() and path.is_file():
        tick_print("Removing 'pyproject.toml' file")
        pyproject_toml_io_manager._opener.open = False
        path.unlink()
