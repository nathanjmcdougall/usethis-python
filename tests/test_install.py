import shutil
from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from usethis._config import usethis_config
from usethis._integrations.backend.uv.call import call_uv_subprocess
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._subprocess import call_subprocess
from usethis._test import change_cwd


@pytest.fixture
def usethis_installed_dir(
    uv_init_dir: Path, usethis_dev_dir: Path
) -> Generator[Path, None, None]:
    with TemporaryDirectory() as tmp_path:
        # Make a copy of the current usethis codebase to avoid interacting with pytest
        copy_usethis_dev_dir = Path(tmp_path) / "usethis-python"
        shutil.copytree(
            usethis_dev_dir,
            copy_usethis_dev_dir,
            # The git repo is too big and we don't need it
            # Also ignore the virtual environment
            ignore=shutil.ignore_patterns(".git", ".venv"),
            symlinks=True,
        )

        with change_cwd(copy_usethis_dev_dir):
            # Initialize a git repository so the package can be built (since it relies
            # on vcs)
            call_subprocess(["git", "init"])
            call_subprocess(["git", "add", "."])
            call_subprocess(["git", "commit", "-m", "Initial commit"])

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            # Install usethis in a virtual environment
            call_uv_subprocess(
                ["add", f"{copy_usethis_dev_dir.as_posix()}"], change_toml=True
            )

        yield uv_init_dir


class TestInstalledInOwnVenv:
    def test_help(self, usethis_installed_dir: Path):
        with change_cwd(usethis_installed_dir):
            # Should run without error
            call_subprocess(["usethis", "--help"])

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_add_pytest(self, usethis_installed_dir: Path):
        with change_cwd(usethis_installed_dir):
            # Should run without error
            if not usethis_config.offline:
                call_subprocess(["usethis", "tool", "pytest"])
            else:
                call_subprocess(["usethis", "tool", "pytest", "--offline"])
