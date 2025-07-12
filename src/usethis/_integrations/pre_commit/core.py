from __future__ import annotations

from usethis._config import usethis_config
from usethis._console import box_print, info_print, tick_print
from usethis._integrations.backend.uv.call import call_uv_subprocess
from usethis._integrations.backend.uv.errors import UVSubprocessFailedError
from usethis._integrations.backend.uv.used import is_uv_used
from usethis._integrations.pre_commit.errors import PreCommitInstallationError


def remove_pre_commit_config() -> None:
    name = ".pre-commit-config.yaml"
    if not (usethis_config.cpd() / name).exists():
        # Early exit; the file already doesn't exist
        return

    tick_print(f"Removing '{name}'.")
    (usethis_config.cpd() / name).unlink()


def install_pre_commit_hooks() -> None:
    """Install pre-commit hooks.

    Note that this requires pre-commit to be installed. It also requires the user to be
    in a git repo.
    """
    if usethis_config.frozen:
        if is_uv_used():
            box_print("Run 'uv run pre-commit install' to register pre-commit.")
        else:
            box_print("Run 'pre-commit install' to register pre-commit.")
        return

    tick_print("Ensuring pre-commit is installed to Git.")
    try:
        call_uv_subprocess(["run", "pre-commit", "install"], change_toml=False)
    except UVSubprocessFailedError as err:
        msg = f"Failed to install pre-commit in the Git repository:\n{err}"
        raise PreCommitInstallationError(msg) from None
    tick_print("Ensuring pre-commit hooks are installed.")
    info_print(
        "This may take a minute or so while the hooks are downloaded.", temporary=True
    )
    try:
        call_uv_subprocess(["run", "pre-commit", "install-hooks"], change_toml=False)
    except UVSubprocessFailedError as err:
        msg = f"Failed to install pre-commit hooks:\n{err}"
        raise PreCommitInstallationError(msg) from None


def uninstall_pre_commit_hooks() -> None:
    """Uninstall pre-commit hooks.

    Note that this requires the user to be in a git repo.
    """
    if usethis_config.frozen:
        box_print(
            "Run 'uv run --with pre-commit pre-commit uninstall' to deregister pre-commit."
        )
        return

    tick_print("Ensuring pre-commit hooks are uninstalled.")
    try:
        call_uv_subprocess(
            ["run", "--with", "pre-commit", "pre-commit", "uninstall"],
            change_toml=False,
        )
    except UVSubprocessFailedError as err:
        msg = f"Failed to uninstall pre-commit hooks:\n{err}"
        raise PreCommitInstallationError(msg) from None
