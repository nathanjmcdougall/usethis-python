from pathlib import Path

from usethis._console import tick_print
from usethis._integrations.pre_commit.errors import PreCommitInstallationError
from usethis._integrations.uv.call import call_uv_subprocess
from usethis._integrations.uv.errors import UVSubprocessFailedError

# TODO make an issue to add usethis tool validate-pyproject or similar.
# I like usethis tool pyproject to add both validate-pyproject, pyproject-fmt, and
# to create the file if it doesn't exist with minimal config.


def remove_pre_commit_config() -> None:
    if not (Path.cwd() / ".pre-commit-config.yaml").exists():
        # Early exit; the file already doesn't exist
        return

    tick_print("Removing .pre-commit-config.yaml file.")
    (Path.cwd() / ".pre-commit-config.yaml").unlink()


def install_pre_commit_hooks() -> None:
    """Install pre-commit hooks.

    Note that this requires pre-commit to be installed. It also requires the user to be
    in a git repo.
    """

    tick_print("Ensuring pre-commit hooks are installed.")
    try:
        call_uv_subprocess(["run", "pre-commit", "install"])
    except UVSubprocessFailedError as err:
        msg = f"Failed to install pre-commit hooks:\n{err}"
        raise PreCommitInstallationError(msg) from None


def uninstall_pre_commit_hooks() -> None:
    """Uninstall pre-commit hooks.

    Note that this requires pre-commit to be installed. It also requires the user to be
    in a git repo.
    """

    tick_print("Ensuring pre-commit hooks are uninstalled.")
    try:
        call_uv_subprocess(["run", "pre-commit", "uninstall"])
    except UVSubprocessFailedError as err:
        msg = f"Failed to uninstall pre-commit hooks:\n{err}"
        raise PreCommitInstallationError(msg) from None
