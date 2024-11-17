import pytest

from usethis._integrations.uv.call import call_subprocess
from usethis._integrations.uv.errors import UVSubprocessFailedError


class TestCallSubprocess:
    def test_help_output_suppressed(self, capfd: pytest.CaptureFixture[str]):
        # Act
        call_subprocess(["help"])

        # Assert
        assert capfd.readouterr().out == ""
        assert capfd.readouterr().err == ""

    def test_nonexistent_command(self):
        # Act and Assert
        msg = (
            "Failed to run uv subprocess:\n"
            "error: unrecognized subcommand 'does-not-exist'"
        )
        with pytest.raises(UVSubprocessFailedError, match=msg):
            call_subprocess(["does-not-exist"])
