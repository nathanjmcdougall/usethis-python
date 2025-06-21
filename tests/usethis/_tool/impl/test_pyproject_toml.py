from pathlib import Path

import pytest


class TestOtherTools:
    def test_in_sync_with_all_tools(self):
        from usethis._tool.all_ import ALL_TOOLS
        from usethis._tool.impl.pyproject_toml import OTHER_TOOLS, PyprojectTOMLTool

        assert {tool.name.lower() for tool in OTHER_TOOLS} | {
            PyprojectTOMLTool().name
        } == {tool.name.lower() for tool in ALL_TOOLS}


class TestPyprojectTOMLTool:
    class TestRemoveManagedFiles:
        def test_warning(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
            # Arrange
            from usethis._config_file import files_manager
            from usethis._test import change_cwd
            from usethis._tool.impl.pyproject_toml import PyprojectTOMLTool

            # Act
            with change_cwd(uv_init_dir), files_manager():
                PyprojectTOMLTool().remove_managed_files()

                out, err = capfd.readouterr()
                assert not err
                assert out == (
                    "☐ Check that important config in 'pyproject.toml' is not lost.\n"
                    "✔ Removing 'pyproject.toml'.\n"
                )

        def test_extra_warning_when_config_exists(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # Arrange
            from usethis._config_file import files_manager
            from usethis._test import change_cwd
            from usethis._tool.impl.pyproject_toml import PyprojectTOMLTool

            (uv_init_dir / "pyproject.toml").write_text(
                """\
[tool.ruff.lint]
select = ["E", "PT"]
"""
            )

            # Act
            with change_cwd(uv_init_dir), files_manager():
                PyprojectTOMLTool().remove_managed_files()

                out, err = capfd.readouterr()
                assert not err
                assert out == (
                    "☐ Check that important config in 'pyproject.toml' is not lost.\n"
                    "☐ The Ruff tool was using 'pyproject.toml' for config, but that file is being \n"
                    "removed. You will need to re-configure it.\n"
                    "✔ Removing 'pyproject.toml'.\n"
                )

    class TestPrintHowToUse:
        @pytest.mark.usefixtures("_vary_network_conn")
        def test_link_isnt_dead(self):
            """A regression test."""
            import requests

            # Arrange
            from usethis._config import usethis_config

            url = (
                "https://packaging.python.org/en/latest/guides/writing-pyproject-toml/"
            )

            if not usethis_config.offline:
                # Act
                result = requests.head(url, timeout=5)

                # Assert
                assert result.status_code == 200

        def test_some_output(self, capfd: pytest.CaptureFixture[str]):
            # Arrange
            from usethis._tool.impl.pyproject_toml import PyprojectTOMLTool

            tool = PyprojectTOMLTool()

            # Act
            tool.print_how_to_use()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out

    class TestName:
        def test_value(self):
            # Arrange
            from usethis._tool.impl.pyproject_toml import PyprojectTOMLTool

            tool = PyprojectTOMLTool()

            # Act
            result = tool.name

            # Assert
            assert result == "pyproject.toml"

    class TestDevDeps:
        def test_none(self):
            # Arrange
            from usethis._tool.impl.pyproject_toml import PyprojectTOMLTool

            tool = PyprojectTOMLTool()

            # Act
            result = tool.get_dev_deps()

            # Assert
            assert result == []
