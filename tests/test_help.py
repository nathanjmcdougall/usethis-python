from pytest_codspeed import BenchmarkFixture


def test_help_flag(benchmark: BenchmarkFixture):
    # Arrange
    from typer.testing import CliRunner

    from usethis._interface.tool import app

    runner = CliRunner()

    # Act
    benchmark(runner.invoke, app, ["--help"])
