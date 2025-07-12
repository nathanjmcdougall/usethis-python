import shutil
from collections.abc import Generator
from enum import Enum
from pathlib import Path

import pytest

from usethis._config import usethis_config
from usethis._integrations.backend.uv.call import call_subprocess, call_uv_subprocess
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
                # Deliberately kept at at a version other than the latest version to
                # check range checks e.g. for Bitbucket pipelines matrixes.
                "3.12",
                "--vcs",
                "none",
            ],
            change_toml=True,
        )

    return tmp_path


@pytest.fixture
def uv_init_dir(tmp_path: Path, _uv_init_dir: Path) -> Generator[Path, None, None]:
    with change_cwd(tmp_path):
        shutil.copytree(
            src=_uv_init_dir, dst=tmp_path, symlinks=True, dirs_exist_ok=True
        )

    with (
        change_cwd(tmp_path),
        usethis_config.set(frozen=True),
    ):
        yield tmp_path


@pytest.fixture
def uv_init_repo_dir(tmp_path: Path, _uv_init_dir: Path) -> Generator[Path, None, None]:
    with change_cwd(tmp_path):
        shutil.copytree(
            src=_uv_init_dir, dst=tmp_path, symlinks=True, dirs_exist_ok=True
        )

        call_subprocess(["git", "init"])

        with (
            change_cwd(tmp_path),
            usethis_config.set(frozen=True),
        ):
            yield tmp_path


@pytest.fixture
def uv_env_dir(uv_init_repo_dir: Path) -> Generator[Path, None, None]:
    """A directory with a git repo, as well as uv-unfrozen project; allow venv and lockfile."""
    with (
        change_cwd(uv_init_repo_dir),
        usethis_config.set(frozen=False),
    ):
        yield uv_init_repo_dir


@pytest.fixture
def bare_dir(tmp_path: Path) -> Generator[Path, None, None]:
    with change_cwd(tmp_path):
        yield tmp_path


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
def _online_status(request: pytest.FixtureRequest) -> NetworkConn:
    assert isinstance(request.param, NetworkConn)

    if request.param is NetworkConn.ONLINE and is_offline():
        pytest.skip("Network connection is offline")

    return request.param


@pytest.fixture(scope="session")
def _vary_network_conn(_online_status: NetworkConn) -> Generator[None, None, None]:
    """Fixture to vary the network connection.

    Use `usethis._config.usethis_config` to check whether things are in offline
    model, since this fixture does not return anything.
    """
    offline = _online_status is NetworkConn.OFFLINE

    usethis_config.offline = offline
    yield
    if offline:
        usethis_config.offline = False


@pytest.fixture
def usethis_dev_dir() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture
def git_path() -> Path:
    """Fixture to get the path to the git executable."""
    git_path = shutil.which("git")

    if not git_path:
        pytest.skip("Git executable not found")

    return Path(git_path)


@pytest.fixture
def uv_path() -> Path:
    """Fixture to get the path to the uv executable."""
    uv_path = shutil.which("uv")

    if not uv_path:
        pytest.skip("uv executable not found")

    return Path(uv_path)
