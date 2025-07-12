from pathlib import Path

import pytest

from usethis._deps import add_deps_to_group
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.pre_commit.core import (
    install_pre_commit_hooks,
    remove_pre_commit_config,
    uninstall_pre_commit_hooks,
)
from usethis._integrations.pre_commit.errors import PreCommitInstallationError
from usethis._integrations.pre_commit.hooks import add_placeholder_hook
from usethis._test import change_cwd
from usethis._types.deps import Dependency


class TestRemovePreCommitConfig:
    def test_exists(self, tmp_path: Path):
        # Arrange
        (tmp_path / ".pre-commit-config.yaml").touch()

        # Act
        with change_cwd(tmp_path):
            remove_pre_commit_config()

        # Assert
        assert not (tmp_path / ".pre-commit-config.yaml").exists()

    def test_message(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        (uv_init_dir / ".pre-commit-config.yaml").touch()

        # Act
        with change_cwd(uv_init_dir):
            remove_pre_commit_config()

        # Assert
        out, _ = capfd.readouterr()
        assert out == "✔ Removing '.pre-commit-config.yaml'.\n"

    def test_already_missing(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
        # Act
        with change_cwd(tmp_path):
            remove_pre_commit_config()

        # Assert
        out, _ = capfd.readouterr()
        assert out == ""
        assert not (tmp_path / ".pre-commit-config.yaml").exists()

    def test_does_not_exist(self, tmp_path: Path):
        # Act
        with change_cwd(tmp_path):
            remove_pre_commit_config()

        # Assert
        assert not (tmp_path / ".pre-commit-config.yaml").exists()


class TestInstallPreCommitHooks:
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_message(self, uv_env_dir: Path, capfd: pytest.CaptureFixture[str]):
        # This is needed to check the standard (non-frozen) message

        # Arrange
        with change_cwd(uv_env_dir), PyprojectTOMLManager():
            add_deps_to_group([Dependency(name="pre-commit")], "dev")
            add_placeholder_hook()
            capfd.readouterr()

            # Act
            install_pre_commit_hooks()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Ensuring pre-commit is installed to Git.\n"
                "✔ Ensuring pre-commit hooks are installed.\n"
                "ℹ This may take a minute or so while the hooks are downloaded.\r"  # noqa: RUF001
            )

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_frozen_message_using_uv(
        self, uv_init_repo_dir: Path, capfd: pytest.CaptureFixture[str]
    ):
        # Arrange
        with change_cwd(uv_init_repo_dir), PyprojectTOMLManager():
            add_deps_to_group([Dependency(name="pre-commit")], "dev")
            add_placeholder_hook()
            capfd.readouterr()

            # Act
            install_pre_commit_hooks()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "☐ Run 'uv run pre-commit install' to register pre-commit.\n"
            )

    def test_err(self, tmp_path: Path):
        # Act, Assert
        with change_cwd(tmp_path), pytest.raises(PreCommitInstallationError):
            # Will fail because pre-commit isn't installed.
            install_pre_commit_hooks()


class TestUninstallPreCommitHooks:
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_message_and_file(
        self,
        uv_env_dir: Path,
        capfd: pytest.CaptureFixture[str],
    ):
        # This is needed to check the standard (non-frozen) message

        # Arrange
        with change_cwd(uv_env_dir), PyprojectTOMLManager():
            add_deps_to_group([Dependency(name="pre-commit")], "dev")
            add_placeholder_hook()
            capfd.readouterr()

            # Act
            uninstall_pre_commit_hooks()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == "✔ Ensuring pre-commit hooks are uninstalled.\n"

        # Uninstalling the hooks shouldn't remove the config file
        assert (uv_env_dir / ".pre-commit-config.yaml").exists()

    def test_err(self, tmp_path: Path):
        # Act, Assert
        with change_cwd(tmp_path), pytest.raises(PreCommitInstallationError):
            # Will fail because pre-commit isn't installed.
            uninstall_pre_commit_hooks()
