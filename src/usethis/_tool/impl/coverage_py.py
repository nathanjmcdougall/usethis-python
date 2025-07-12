from __future__ import annotations

from pathlib import Path

from usethis._config_file import (
    CoverageRCManager,
    ToxINIManager,
)
from usethis._console import box_print
from usethis._integrations.backend.uv.used import is_uv_used
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.file.setup_cfg.io_ import SetupCFGManager
from usethis._integrations.project.layout import get_source_dir_str
from usethis._tool.base import Tool
from usethis._tool.config import ConfigEntry, ConfigItem, ConfigSpec
from usethis._types.deps import Dependency


class CoveragePyTool(Tool):
    # https://github.com/nedbat/coveragepy

    @property
    def name(self) -> str:
        return "Coverage.py"

    def print_how_to_use(self) -> None:
        from usethis._tool.impl.pytest import PytestTool

        if PytestTool().is_used():
            if is_uv_used():
                box_print(
                    f"Run 'uv run pytest --cov' to run your tests with {self.name}."
                )
            else:
                box_print(f"Run 'pytest --cov' to run your tests with {self.name}.")
        elif is_uv_used():
            box_print(
                f"Run 'uv run coverage help' to see available {self.name} commands."
            )
        else:
            box_print(f"Run 'coverage help' to see available {self.name} commands.")

    def get_test_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        from usethis._tool.impl.pytest import PytestTool

        deps = [Dependency(name="coverage", extras=frozenset({"toml"}))]
        if unconditional or PytestTool().is_used():
            deps += [Dependency(name="pytest-cov")]
        return deps

    def get_config_spec(self) -> ConfigSpec:
        # https://coverage.readthedocs.io/en/latest/config.html#configuration-reference

        exclude_also = [
            "if TYPE_CHECKING:",
            "raise AssertionError",
            "raise NotImplementedError",
            "assert_never(.*)",
            "class .*\\bProtocol\\):",
            "@(abc\\.)?abstractmethod",
        ]
        omit = ["*/pytest-of-*/*"]

        def _get_source():
            return [get_source_dir_str()]

        return ConfigSpec.from_flat(
            file_managers=[
                CoverageRCManager(),
                SetupCFGManager(),
                ToxINIManager(),
                PyprojectTOMLManager(),
            ],
            resolution="first",
            config_items=[
                ConfigItem(
                    description="Overall Config",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=[]),
                        # N.B. other ini files use a "coverage:" prefix so there's no
                        # section corresponding to overall config
                        Path("pyproject.toml"): ConfigEntry(keys=["tool", "coverage"]),
                    },
                    applies_to_all=False,
                ),
                ConfigItem(
                    description="Run Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=["run"]),
                        Path("setup.cfg"): ConfigEntry(keys=["coverage:run"]),
                        Path("tox.ini"): ConfigEntry(keys=["coverage:run"]),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "run"]
                        ),
                    },
                ),
                ConfigItem(
                    description="Source Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(
                            keys=["run", "source"], get_value=_get_source
                        ),
                        Path("setup.cfg"): ConfigEntry(
                            keys=["coverage:run", "source"], get_value=_get_source
                        ),
                        Path("tox.ini"): ConfigEntry(
                            keys=["coverage:run", "source"], get_value=_get_source
                        ),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "run", "source"],
                            get_value=_get_source,
                        ),
                    },
                ),
                ConfigItem(
                    description="Report Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=["report"]),
                        Path("setup.cfg"): ConfigEntry(keys=["coverage:report"]),
                        Path("tox.ini"): ConfigEntry(keys=["coverage:report"]),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "report"]
                        ),
                    },
                ),
                ConfigItem(
                    description="Exclude Also Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(
                            keys=["report", "exclude_also"],
                            get_value=lambda: exclude_also,
                        ),
                        Path("setup.cfg"): ConfigEntry(
                            keys=["coverage:report", "exclude_also"],
                            get_value=lambda: exclude_also,
                        ),
                        Path("tox.ini"): ConfigEntry(
                            keys=["coverage:report", "exclude_also"],
                            get_value=lambda: exclude_also,
                        ),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "report", "exclude_also"],
                            get_value=lambda: exclude_also,
                        ),
                    },
                ),
                ConfigItem(
                    description="Omit Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(
                            keys=["report", "omit"], get_value=lambda: omit
                        ),
                        Path("setup.cfg"): ConfigEntry(
                            keys=["coverage:report", "omit"], get_value=lambda: omit
                        ),
                        Path("tox.ini"): ConfigEntry(
                            keys=["coverage:report", "omit"], get_value=lambda: omit
                        ),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "report", "omit"],
                            get_value=lambda: omit,
                        ),
                    },
                ),
                ConfigItem(
                    description="Paths Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=["paths"]),
                        Path("setup.cfg"): ConfigEntry(keys=["coverage:paths"]),
                        Path("tox.ini"): ConfigEntry(keys=["coverage:paths"]),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "paths"],
                        ),
                    },
                ),
                ConfigItem(
                    description="HTML Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=["html"]),
                        Path("setup.cfg"): ConfigEntry(keys=["coverage:html"]),
                        Path("tox.ini"): ConfigEntry(keys=["coverage:html"]),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "html"]
                        ),
                    },
                ),
                ConfigItem(
                    description="XML Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=["xml"]),
                        Path("setup.cfg"): ConfigEntry(keys=["coverage:xml"]),
                        Path("tox.ini"): ConfigEntry(keys=["coverage:xml"]),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "xml"]
                        ),
                    },
                ),
                ConfigItem(
                    description="JSON Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=["json"]),
                        Path("setup.cfg"): ConfigEntry(keys=["coverage:json"]),
                        Path("tox.ini"): ConfigEntry(keys=["coverage:json"]),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "json"]
                        ),
                    },
                ),
                ConfigItem(
                    description="LCOV Configuration",
                    root={
                        Path(".coveragerc"): ConfigEntry(keys=["lcov"]),
                        Path("setup.cfg"): ConfigEntry(keys=["coverage:lcov"]),
                        Path("tox.ini"): ConfigEntry(keys=["coverage:lcov"]),
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "coverage", "lcov"]
                        ),
                    },
                ),
            ],
        )

    def get_managed_files(self) -> list[Path]:
        return [Path(".coveragerc")]
