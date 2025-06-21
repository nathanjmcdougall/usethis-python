from pathlib import Path


class TestBitbucket:
    def test_readme_example(self, tmp_path: Path):
        """This example is used the README.md file.

        Note carefully! If this test is updated, the README.md file must be
        updated too.
        """
        # Arrange
        from typer.testing import CliRunner

        from usethis._interface.ci import app
        from usethis._test import change_cwd

        # We've already run ruff and pytest...
        (tmp_path / "pytest.ini").touch()
        (tmp_path / "ruff.toml").touch()
        # Consistent versions in the matrix - only two to demonstrate it, 3 is excessive
        (tmp_path / "pyproject.toml").write_text(
            """\
[project]
requires-python = ">=3.12"
"""
        )

        # Act
        runner = CliRunner()
        with change_cwd(tmp_path):
            result = runner.invoke(app, [])

        # Assert
        assert result.exit_code == 0, result.output
        assert (
            result.output
            == """\
✔ Writing 'bitbucket-pipelines.yml'.
✔ Adding cache 'uv' definition to 'bitbucket-pipelines.yml'.
✔ Adding 'Run Ruff' to default pipeline in 'bitbucket-pipelines.yml'.
✔ Adding 'Run Ruff Formatter' to default pipeline in 'bitbucket-pipelines.yml'.
✔ Adding 'Test on 3.12' to default pipeline in 'bitbucket-pipelines.yml'.
✔ Adding 'Test on 3.13' to default pipeline in 'bitbucket-pipelines.yml'.
☐ Run your pipeline via the Bitbucket website.
"""
        )
