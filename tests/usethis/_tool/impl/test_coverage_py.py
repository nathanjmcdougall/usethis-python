from pathlib import Path

from usethis._config_file import files_manager
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._test import change_cwd
from usethis._tool.impl.coverage_py import CoveragePyTool


class TestCoveragePyTool:
    class TestAddConfigs:
        def test_after_codespell(self, tmp_path: Path):
            # To check the config is valid
            # https://github.com/usethis-python/usethis-python/issues/558

            # Arrange
            (tmp_path / "pyproject.toml").write_text("""\
[project]
name = "example"
version = "0.1.0"
description = "Add your description here"

[dependency-groups]
dev = [
    "codespell>=2.4.1",
]
                                                    
[tool.codespell]
ignore-regex = ["[A-Za-z0-9+/]{100,}"]
""")

            # Act
            with change_cwd(tmp_path), files_manager():
                CoveragePyTool().add_configs()

            # Assert
            with change_cwd(tmp_path), files_manager():
                assert ["tool", "coverage"] in PyprojectTOMLManager()
            assert "[tool.coverage]" in (tmp_path / "pyproject.toml").read_text()
