import shutil
from collections.abc import Generator
from enum import Enum
from pathlib import Path

import pytest

from usethis._config import usethis_config
from usethis._integrations.uv.call import call_subprocess, call_uv_subprocess
from usethis._test import change_cwd, is_offline


@pytest.fixture(scope="session")
def _uv_init_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    tmp_path = tmp_path_factory.mktemp("uv_init")
    with change_cwd(tmp_path):
        call_uv_subprocess(
            [
                "init",
                "--lib",
                "--python",
                "3.12",
                "--vcs",
                "none",
            ]
        )

    return tmp_path


@pytest.fixture
def uv_init_dir(tmp_path: Path, _uv_init_dir: Path) -> Generator[Path, None, None]:
    with change_cwd(tmp_path):
        shutil.copytree(
            src=_uv_init_dir, dst=tmp_path, symlinks=True, dirs_exist_ok=True
        )

    with usethis_config.set(frozen=True):
        yield tmp_path


@pytest.fixture
def uv_init_repo_dir(tmp_path: Path, _uv_init_dir: Path) -> Generator[Path, None, None]:
    with change_cwd(tmp_path):
        shutil.copytree(
            src=_uv_init_dir, dst=tmp_path, symlinks=True, dirs_exist_ok=True
        )

        call_subprocess(["git", "init"])

    with usethis_config.set(frozen=True):
        yield tmp_path


@pytest.fixture
def uv_env_dir(uv_init_repo_dir: Path) -> Generator[Path, None, None]:
    """A directory with a git repo, as well as uv-unfrozen project; allow venv and lockfile."""
    with change_cwd(uv_init_repo_dir), usethis_config.set(frozen=False):
        yield uv_init_repo_dir


class NetworkConn(Enum):
    OFFLINE = 0
    ONLINE = 1


@pytest.fixture(
    params=[
        NetworkConn.ONLINE,  # Run online first since we want to populate caches
        NetworkConn.OFFLINE,
    ],
    scope="session",
)
def _vary_network_conn(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Fixture to vary the network connection; returns True if offline."""
    if request.param is NetworkConn.ONLINE and is_offline():
        pytest.skip("Network connection is offline")

    offline = request.param is NetworkConn.OFFLINE

    usethis_config.offline = offline
    yield
    usethis_config.offline = False


@pytest.fixture
def usethis_dev_dir() -> Path:
    return Path(__file__).parent.parent
