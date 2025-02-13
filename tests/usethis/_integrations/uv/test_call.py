from pathlib import Path

import pytest

import usethis._integrations.uv.call
from usethis._config import usethis_config
from usethis._integrations.uv.call import call_uv_subprocess
from usethis._integrations.uv.errors import UVSubprocessFailedError
from usethis._test import change_cwd


class TestCallUVSubprocess:
    def test_help_output_suppressed(self, capfd: pytest.CaptureFixture[str]):
        # Act
        call_uv_subprocess(["help"])

        # Assert
        assert capfd.readouterr().out == ""
        assert capfd.readouterr().err == ""

    def test_nonexistent_command(self):
        # Act and Assert
        match = ".*error: unrecognized subcommand 'does-not-exist'.*"
        with pytest.raises(UVSubprocessFailedError, match=match):
            call_uv_subprocess(["does-not-exist"])

    def test_frozen_added_in_uv_run(self, monkeypatch: pytest.MonkeyPatch):
        # Mock the usethis._subprocess.call_subprocess function to check args passed

        # Arrange
        # Mock the call_subprocess function to check the args passed
        def mock_call_subprocess(args: list[str]) -> str:
            return " ".join(args)

        monkeypatch.setattr(
            usethis._integrations.uv.call, "call_subprocess", mock_call_subprocess
        )

        with usethis_config.set(frozen=True):
            # Act, Assert
            # Check the args passed to call_subprocess
            assert call_uv_subprocess(["run", "pre-commit", "install"]) == (
                "uv run --frozen pre-commit install"
            )

    def test_handle_missing_version(
        self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
    ):
        # https://github.com/nathanjmcdougall/usethis-python/issues/299

        # Arrange
        (tmp_path / "pyproject.toml").write_text(
            """\
[project]
name = "example"
"""
        )

        # Act
        with change_cwd(tmp_path):
            call_uv_subprocess(["add", "ruff==0.9.0"])

        # Assert
        assert (
            (tmp_path / "pyproject.toml").read_text()
            == """\
[project]
name = "example"
version = "0.1.0"
dependencies = [
    "ruff==0.9.0",
]
"""
        )
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Set project version to '0.1.0' in 'pyproject.toml'.\n"
