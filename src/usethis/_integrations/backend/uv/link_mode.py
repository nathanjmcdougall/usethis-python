import contextlib

from usethis._integrations.backend.uv.toml import UVTOMLManager
from usethis._integrations.file.pyproject_toml.errors import (
    PyprojectTOMLValueAlreadySetError,
)
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager


def ensure_symlink_mode() -> None:
    """Ensure that the symlink link mode is enabled.

    This is a temporary workaround until uv handles venvs better for this situation
    in Windows.

    See here for more information: https://github.com/astral-sh/uv/issues/11134
    """
    # The reason we don't do this for just Windows is because repo configuration should
    # ideally be valid cross-platform.
    if UVTOMLManager().path.exists():
        with contextlib.suppress(PyprojectTOMLValueAlreadySetError):
            UVTOMLManager().set_value(
                keys=["link-mode"], value="symlink", exists_ok=False
            )
    else:
        PyprojectTOMLManager().path.touch()
        with contextlib.suppress(PyprojectTOMLValueAlreadySetError):
            PyprojectTOMLManager().set_value(
                keys=["tool", "uv", "link-mode"], value="symlink", exists_ok=False
            )
