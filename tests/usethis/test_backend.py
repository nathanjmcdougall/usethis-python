from pathlib import Path

import pytest

import usethis._integrations.backend.uv.available
from usethis._backend import get_backend
from usethis._config import usethis_config
from usethis._config_file import files_manager
from usethis._integrations.backend.uv.errors import UVSubprocessFailedError
from usethis._test import change_cwd
from usethis._types.backend import BackendEnum


class TestGetBackend:
    def test_non_auto_remains(self):
        for backend in BackendEnum:
            if backend is not BackendEnum.auto:
                with usethis_config.set(backend=backend):
                    assert get_backend() == backend

    def test_uv_used(self, tmp_path: Path):
        # Arrange
        (tmp_path / "uv.lock").touch()

        # Act
        with change_cwd(tmp_path), usethis_config.set(backend=BackendEnum.auto):
            result = get_backend()

        # Assert
        assert result == BackendEnum.uv

    def test_uv_not_used_but_available(self, tmp_path: Path):
        # Act
        with (
            change_cwd(tmp_path),
            usethis_config.set(backend=BackendEnum.auto),
            files_manager(),
        ):
            result = get_backend()

        # Assert
        assert result == BackendEnum.uv

    def test_uv_not_used_and_not_available(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange

        def mock_call_uv_subprocess(*_, **__):
            raise UVSubprocessFailedError

        monkeypatch.setattr(
            usethis._integrations.backend.uv.available,
            "call_uv_subprocess",
            mock_call_uv_subprocess,
        )

        # Act
        with (
            change_cwd(tmp_path),
            usethis_config.set(backend=BackendEnum.auto),
            files_manager(),
        ):
            result = get_backend()

        # Assert
        assert result == BackendEnum.none
