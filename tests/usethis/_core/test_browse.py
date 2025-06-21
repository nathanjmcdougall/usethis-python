import pytest


class TestPyPI:
    def test_message(self, capfd: pytest.CaptureFixture[str]):
        # Arrange

        from usethis._core.browse import browse_pypi

        # Act
        browse_pypi(package="numpy", browser=False)

        # Assert
        out, err = capfd.readouterr()
        assert not err
        assert "☐ Open URL <https://pypi.org/project/numpy/>." in out

    def test_open_in_browser(self, monkeypatch):
        # Arrange
        import typer

        from usethis._core.browse import browse_pypi

        class MockLaunch:
            def __init__(self):
                self.url = None

            def __call__(self, url):
                self.url = url

        mock_launch = MockLaunch()
        monkeypatch.setattr(typer, "launch", mock_launch)

        # Act
        browse_pypi(package="numpy", browser=True)

        # Assert
        assert mock_launch.url == "https://pypi.org/project/numpy/"
