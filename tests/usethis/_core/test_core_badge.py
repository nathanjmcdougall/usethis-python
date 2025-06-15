from pathlib import Path

import pytest

from usethis._core.badge import Badge, add_badge, is_badge, remove_badge
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._test import change_cwd


class TestIsBadge:
    def test_badge_no_braces(self):
        # Arrange
        txt = """![Ruff](https://example.com)"""

        # Act
        result = is_badge(txt)

        # Assert
        assert result

    def test_badge_with_braces(self):
        # Arrange
        txt = """![Ruff](<https://example.com>)"""

        # Act
        result = is_badge(txt)

        # Assert
        assert result

    def test_badge_with_link(self):
        # Arrange
        txt = """[![Ruff](<https://example.com>)](https://example.com)"""

        # Act
        result = is_badge(txt)

        # Assert
        assert result

    def test_not_badge(self):
        # Arrange
        txt = """# Header"""

        # Act
        result = is_badge(txt)

        # Assert
        assert not result


class TestAddBadge:
    def test_no_readme(self, bare_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="![Licence](https://img.shields.io/badge/licence-mit-green)",
                )
            )

        # Assert (that the badge markdown is printed)
        out, err = capfd.readouterr()
        assert not err
        assert out == (
            "✔ Writing 'README.md'.\n"
            "☐ Populate 'README.md' to help users understand the project.\n"
            "✔ Adding Licence badge to 'README.md'.\n"
        )

    def test_not_markdown(self, bare_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        path = bare_dir / "README.foo"
        path.write_text("# Header\n")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="![Licence](https://img.shields.io/badge/licence-mit-green)",
                )
            )

        # Assert (that the badge markdown is printed)
        out, err = capfd.readouterr()
        assert not err
        assert out == (
            "⚠ No Markdown-based README file found, printing badge markdown instead...\n"
            "![Licence](https://img.shields.io/badge/licence-mit-green)\n"
        )

    def test_empty(self, bare_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="![Licence](https://img.shields.io/badge/licence-mit-green)"
                ),
            )

        # Assert
        assert (
            (bare_dir / "README.md").read_text()
            == """\
# test_empty0

![Licence](https://img.shields.io/badge/licence-mit-green)
"""
        )
        out, err = capfd.readouterr()
        assert not err
        assert out == (
            "✔ Writing 'README.md'.\n"
            "☐ Populate 'README.md' to help users understand the project.\n"
            "✔ Adding Licence badge to 'README.md'.\n"
        )

    def test_only_newline(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\

""")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="![Licence](https://img.shields.io/badge/licence-mit-green)"
                )
            )

        # Assert
        assert (
            (bare_dir / "README.md").read_text()
            == """\
# test_only_newline0

![Licence](https://img.shields.io/badge/licence-mit-green)
"""
        )

    def test_predecessor(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
""")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)",
                )
            )

        # Assert
        content = path.read_text()
        assert (
            content
            == """\
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
"""
        )

    def test_not_predecessor(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
""")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)",
                )
            )

        # Assert
        content = path.read_text()
        assert (
            content
            == """\
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
"""
        )

    def test_not_recognized_gets_put_after_known_order(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
""")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="![Don't Know What This Is](https://example.com)",
                )
            )

        # Assert
        content = path.read_text()
        assert (
            content
            == """\
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![Don't Know What This Is](https://example.com)
"""
        )

    def test_skip_header1(self, bare_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
# Header
""")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="![Licence](https://img.shields.io/badge/licence-mit-green)",
                )
            )

        # Assert
        assert (
            path.read_text()
            == """\
# Header

![Licence](https://img.shields.io/badge/licence-mit-green)
"""
        )
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Adding Licence badge to 'README.md'.\n"

    def test_skip_header2(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
## Header
""")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="![Licence](https://img.shields.io/badge/licence-mit-green)",
                )
            )

        # Assert
        assert (
            path.read_text()
            == """\
## Header

![Licence](https://img.shields.io/badge/licence-mit-green)
"""
        )

    def test_skip_header_with_extra_newline(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
# Header

""")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="![Licence](https://img.shields.io/badge/licence-mit-green)",
                )
            )

        # Assert
        assert (
            path.read_text()
            == """\
# Header

![Licence](https://img.shields.io/badge/licence-mit-green)
"""
        )

    def test_extra_unstripped_space(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
  # Header  
  
 [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
""")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)",
                )
            )

        # Assert
        content = path.read_text()
        assert (
            content
            == """\
  # Header  
  
 [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
"""
        )

    def test_already_exists(self, bare_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
![Licence](https://img.shields.io/badge/licence-mit-green)
""")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="![Licence](https://img.shields.io/badge/licence-mit-green)",
                )
            )

        # Assert
        assert (
            path.read_text()
            == """\
![Licence](https://img.shields.io/badge/licence-mit-green)
"""
        )
        out, err = capfd.readouterr()
        assert not err
        assert not out

    def test_badge_followed_by_text(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
# Header

Some text
""")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="![Licence](https://img.shields.io/badge/licence-mit-green)",
                )
            )

        # Assert
        assert (
            path.read_text()
            == """\
# Header

![Licence](https://img.shields.io/badge/licence-mit-green)

Some text
"""
        )

    def test_predecessor_based_on_name(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
![Ruff](https://example.com)
""")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="![pre-commit](https://example.com)",
                )
            )

        # Assert
        assert (
            path.read_text()
            == """\
![Ruff](https://example.com)
![pre-commit](https://example.com)
"""
        )

    def test_recognized_gets_put_before_unknown(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
![Don't Know What This Is](https://example.com)
""")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="![Ruff](https://example.com)",
                )
            )

        # Assert
        assert (
            path.read_text()
            == """\
![Ruff](https://example.com)
![Don't Know What This Is](https://example.com)
"""
        )

    def test_already_exists_no_newline_added(self, bare_dir: Path):
        # Arrange
        path = bare_dir / Path("README.md")
        content = """![Ruff](https://example.com)"""
        path.write_text(content)

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(Badge(markdown="![Ruff](https://example.com)"))

        # Assert
        assert path.read_text() == content

    def test_no_unnecessary_spaces(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
# usethis

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json>)](<https://github.com/astral-sh/ruff)

Automate Python project setup and development tasks that are otherwise performed manually.
""")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit>)](<https://github.com/pre-commit/pre-commit)",
                )
            )

        # Assert
        content = path.read_text()
        assert (
            content
            == """\
# usethis

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json>)](<https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit>)](<https://github.com/pre-commit/pre-commit)

Automate Python project setup and development tasks that are otherwise performed manually.
"""
        )

    def test_already_exists_out_of_order(
        self, bare_dir: Path, capfd: pytest.CaptureFixture[str]
    ):
        # Arrange
        path = bare_dir / "README.md"
        content = """\
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit>)](<https://github.com/pre-commit/pre-commit
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json>)](<https://github.com/astral-sh/ruff)
"""
        path.write_text(content)

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json>)](<https://github.com/astral-sh/ruff)",
                )
            )

        # Assert
        assert path.read_text() == content
        out, err = capfd.readouterr()
        assert not err
        assert not out

    def test_skip_html_block(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
<h1 align="center">
  <img src="doc/logo.svg"><br>
</h1>

# usethis
                        
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json>)](<https://github.com/astral-sh/ruff)
""")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit>)](<https://github.com/pre-commit/pre-commit)"
                )
            )

        # Assert
        content = path.read_text()
        assert (
            content
            == """\
<h1 align="center">
  <img src="doc/logo.svg"><br>
</h1>

# usethis
                        
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json>)](<https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit>)](<https://github.com/pre-commit/pre-commit)
"""
        )

    def test_add_to_no_file_extension_readme(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README"
        path.write_text("""\
# usethis
""")

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="[![Ruff](https://example.com>)](<https://example.com)",
                )
            )

        # Assert
        assert not path.with_suffix(".md").exists()
        assert (
            path.read_text()
            == """\
# usethis

[![Ruff](https://example.com>)](<https://example.com)
"""
        )

    def test_wrong_readme_encoding(
        self, bare_dir: Path, capfd: pytest.CaptureFixture[str]
    ):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text(
            """\
# usethis
""",
            encoding="utf-16",
        )

        # Act
        with change_cwd(bare_dir), PyprojectTOMLManager():
            add_badge(
                Badge(
                    markdown="[![Ruff](https://example.com>)](<https://example.com)",
                )
            )

        # Assert
        out, err = capfd.readouterr()
        assert not err
        assert "encoding" in out


class TestRemoveBadge:
    def test_empty(self, bare_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        path = bare_dir / "README.md"
        path.touch()

        # Act
        with change_cwd(bare_dir):
            remove_badge(
                Badge(
                    markdown="![Licence](https://img.shields.io/badge/licence-mit-green)"
                )
            )

        # Assert
        content = path.read_text()
        assert not content
        out, err = capfd.readouterr()
        assert not err
        assert not out

    def test_single(self, bare_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
![Licence](https://img.shields.io/badge/licence-mit-green)
""")

        # Act
        with change_cwd(bare_dir):
            remove_badge(
                Badge(
                    markdown="![Licence](https://img.shields.io/badge/licence-mit-green)",
                )
            )

        # Assert
        content = path.read_text()
        assert content == "\n"
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Removing Licence badge from 'README.md'.\n"

    def test_no_reademe_file(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README.md"

        # Act
        with change_cwd(bare_dir):
            remove_badge(
                Badge(
                    markdown="![Licence](https://img.shields.io/badge/licence-mit-green)",
                )
            )

        # Assert
        assert not path.exists()

    def test_header_and_text(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
# Header

![Licence](https://img.shields.io/badge/licence-mit-green)
                        
And some text
""")

        # Act
        with change_cwd(bare_dir):
            remove_badge(
                Badge(
                    markdown="![Licence](https://img.shields.io/badge/licence-mit-green)",
                )
            )

        # Assert
        assert (
            path.read_text()
            == """\
# Header

And some text
"""
        )

    def test_multiple_badges(self, bare_dir: Path):
        # Arrange
        path = bare_dir / "README.md"
        path.write_text("""\
![Ruff](https://example.com)
![pre-commit](https://example.com)
""")

        # Act
        with change_cwd(bare_dir):
            remove_badge(
                Badge(
                    markdown="![Ruff](https://example.com)",
                )
            )

        # Assert
        assert (
            path.read_text()
            == """\
![pre-commit](https://example.com)
"""
        )

    def test_no_badges_but_header_and_text(self, bare_dir: Path):
        # Arrange
        path = bare_dir / Path("README.md")
        content = """\
# Header

And some text
"""
        path.write_text(content)

        # Act
        with change_cwd(bare_dir):
            remove_badge(
                Badge(
                    markdown="![Licence](https://img.shields.io/badge/licence-mit-green)",
                )
            )

        # Assert
        assert path.read_text() == content

    def test_already_exists_no_newline_added(self, bare_dir: Path):
        # Arrange
        path = bare_dir / Path("README.md")
        content = """Nothing will be removed"""
        path.write_text(content)

        # Act
        with change_cwd(bare_dir):
            remove_badge(Badge(markdown="![Ruff](https://example.com)"))

        # Assert
        assert path.read_text() == content
