import pytest


class TestPlainPrint:
    def test_out(self, capfd: pytest.CaptureFixture[str]) -> None:
        # Arrange
        from usethis._console import plain_print

        # Act
        plain_print("Hello")

        # Assert
        out, _ = capfd.readouterr()
        assert out == "Hello\n"


class TestTablePrint:
    def test_out(self, capfd: pytest.CaptureFixture[str]) -> None:
        # Arrange
        from rich.table import Table

        from usethis._console import table_print

        # Act
        table_print(
            Table(
                "hello",
                title="Hello",
                show_lines=True,
                box=None,
            )
        )

        # Assert
        out, _ = capfd.readouterr()
        assert "hello" in out
        assert "Hello" in out


class TestTickPrint:
    def test_out(self, capfd: pytest.CaptureFixture[str]) -> None:
        # Arrange
        from usethis._console import tick_print

        # Act
        tick_print("Hello")

        # Assert
        out, _ = capfd.readouterr()
        assert out == "✔ Hello\n"

    def test_alert_only_suppresses(self, capfd: pytest.CaptureFixture[str]) -> None:
        # Arrange
        from usethis._config import usethis_config
        from usethis._console import tick_print

        # Act
        with usethis_config.set(alert_only=True):
            tick_print("Hello")

        # Assert
        out, err = capfd.readouterr()
        assert not err
        assert not out


class TestBoxPrint:
    def test_out(self, capfd: pytest.CaptureFixture[str]) -> None:
        # Arrange
        from usethis._console import box_print

        # Act
        box_print("Hello")

        # Assert
        out, _ = capfd.readouterr()
        assert out == "☐ Hello\n"


class TestInfoPrint:
    def test_out(self, capfd: pytest.CaptureFixture[str]) -> None:
        # Arrange
        from usethis._console import info_print

        # Act
        info_print("Hello")

        # Assert
        out, _ = capfd.readouterr()
        assert out == "ℹ Hello\n"  # noqa: RUF001


class TestErrPrint:
    def test_out(self, capfd: pytest.CaptureFixture[str]) -> None:
        # Arrange
        from usethis._console import err_print

        # Act
        err_print("Hello")

        # Assert
        out, err = capfd.readouterr()
        assert not out
        assert err == "✗ Hello\n"

    def test_alert_only_doesnt_suppress(
        self, capfd: pytest.CaptureFixture[str]
    ) -> None:
        # Arrange
        from usethis._config import usethis_config
        from usethis._console import err_print

        # Act
        with usethis_config.set(alert_only=False):
            err_print("Hello")

        # Assert
        out, err = capfd.readouterr()
        assert err == "✗ Hello\n"
        assert not out


class TestWarnPrint:
    def test_out(self, capfd: pytest.CaptureFixture[str]) -> None:
        # Arrange
        from usethis._console import warn_print

        # Act
        warn_print("Hello")

        # Assert
        out, err = capfd.readouterr()
        assert not err
        assert out == "⚠ Hello\n"

    def test_alert_only_doesnt_suppress(
        self, capfd: pytest.CaptureFixture[str]
    ) -> None:
        # Arrange
        from usethis._config import usethis_config
        from usethis._console import warn_print

        # Act
        with usethis_config.set(alert_only=False):
            warn_print("Hello")

        # Assert
        out, err = capfd.readouterr()
        assert not err
        assert out == "⚠ Hello\n"
