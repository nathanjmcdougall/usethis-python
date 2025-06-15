from __future__ import annotations

from usethis._config import usethis_config
from usethis._console import tick_print
from usethis._integrations.file.pyproject_toml.errors import PyprojectTOMLInitError
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.uv import call
from usethis._integrations.uv.errors import UVInitError, UVSubprocessFailedError


def opinionated_uv_init() -> None:
    """Subprocess `uv init` with opinionated arguments.

    Pass silently if a `pyproject.toml` file already exists.
    """
    if (usethis_config.cpd() / "pyproject.toml").exists():
        return

    tick_print("Writing 'pyproject.toml' and initializing project.")
    try:
        call.call_uv_subprocess(
            ["init", "--lib", usethis_config.cpd().as_posix()],
            change_toml=True,
        )
    except UVSubprocessFailedError as err:
        msg = f"Failed to create a pyproject.toml file and initialize project:\n{err}"
        raise UVInitError(msg) from None


def ensure_pyproject_toml(*, author: bool = True) -> None:
    """Create a pyproject.toml file using `uv init --bare`."""
    if (usethis_config.cpd() / "pyproject.toml").exists():
        return

    tick_print("Writing 'pyproject.toml'.")
    try:
        author_from = "auto" if author else "none"

        call.call_uv_subprocess(
            [
                "init",
                "--bare",
                "--vcs=none",
                f"--author-from={author_from}",
                "--build-backend",  # https://github.com/usethis-python/usethis-python/issues/347
                "hatch",  # until https://github.com/astral-sh/uv/issues/3957
                usethis_config.cpd().as_posix(),
            ],
            change_toml=True,
        )
    except UVSubprocessFailedError as err:
        msg = f"Failed to create a pyproject.toml file:\n{err}"
        raise PyprojectTOMLInitError(msg) from None

    if not (
        (usethis_config.cpd() / "src").exists()
        and (usethis_config.cpd() / "src").is_dir()
    ):
        # hatch needs to know where to find the package
        PyprojectTOMLManager().set_value(
            keys=["tool", "hatch", "build", "targets", "wheel", "packages"],
            value=["."],
        )
