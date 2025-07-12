import pytest

import usethis._integrations.backend.uv.available
from usethis._integrations.backend.uv.available import is_uv_available
from usethis._integrations.backend.uv.errors import UVSubprocessFailedError


class TestIsUVAvailable:
    def test_available_when_running_test_suite(self):
        # Having uv is a pre-requisite for running the test suite
        assert is_uv_available()

    def test_mock_not_available(self, monkeypatch: pytest.MonkeyPatch):
        # Arrange

        def mock_call_uv_subprocess(*_, **__):
            raise UVSubprocessFailedError

        monkeypatch.setattr(
            usethis._integrations.backend.uv.available,
            "call_uv_subprocess",
            mock_call_uv_subprocess,
        )

        # Act
        result = is_uv_available()

        # Assert
        assert not result, "Expected uv to be unavailable, but it was available."
