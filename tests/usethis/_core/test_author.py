from pathlib import Path


class TestAddAuthor:
    def test_no_authors_yet(self, tmp_path: Path):
        # Arrange
        from usethis._core.author import add_author
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").touch()

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            add_author(
                name="John Cleese",
                email="jc@example.com",
            )

        # Assert
        assert (tmp_path / "pyproject.toml").read_text() == (
            """\

[[project.authors]]
name = "John Cleese"
email = "jc@example.com"
"""
        )

    def test_append(self, tmp_path: Path):
        # Arrange
        from usethis._core.author import add_author
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text(
            """\
[project]
authors = [
    { name="First Contributor" }
]
"""
        )

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            add_author(
                name="John Cleese",
                email="jc@example.com",
            )

        # Assert
        assert (tmp_path / "pyproject.toml").read_text() == (
            """\


[[project.authors]]
name = "First Contributor"
[[project.authors]]
name = "John Cleese"
email = "jc@example.com"
"""
        )

    def test_email_not_provided(self, tmp_path: Path):
        # Arrange
        from usethis._core.author import add_author
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").touch()

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            add_author(name="John Cleese")

        # Assert
        assert (tmp_path / "pyproject.toml").read_text() == (
            """\

[[project.authors]]
name = "John Cleese"
"""
        )

    def test_overwrite(self, tmp_path: Path):
        # Arrange
        from usethis._core.author import add_author
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text(
            """\
[project]

[[project.authors]]
name = "First Contributor"
[[project.authors]]
name = "John Cleese"
email = "jc@example.com"
"""
        )

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            add_author(
                name="Python Dev Team",
                overwrite=True,
            )

        # Assert
        assert (tmp_path / "pyproject.toml").read_text() == (
            """\
[project]

[[project.authors]]
name = "Python Dev Team"
"""
        )

    def test_no_pyproject_yet(self, tmp_path: Path):
        # Arrange
        from usethis._core.author import add_author
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            add_author(name="John Cleese")

        # Assert
        assert "John Cleese" in (tmp_path / "pyproject.toml").read_text()

    def test_doesnt_break_other_sections(self, tmp_path: Path):
        # There is a bug in tomlkit I suspect, we needed a bit of a bespoke workaround.
        # Suspected to be similar to this https://github.com/python-poetry/tomlkit/issues/381

        # Arrange
        from usethis._core.author import add_author
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text(
            """\
[project]
authors = [
  { name = "Python Dev"},
]
scripts.usethis = "usethis.__main__:app"
"""
        )

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager() as manager:
            add_author(name="John Cleese")
            assert ["project", "scripts"] in manager

        # Assert
        with change_cwd(tmp_path), PyprojectTOMLManager() as manager:
            assert ["project"] in manager
            assert ["project", "scripts"] in manager
