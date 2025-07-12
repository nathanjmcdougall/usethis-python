from __future__ import annotations

from pathlib import Path

from typing_extensions import assert_never

from usethis._console import box_print
from usethis._integrations.backend.uv.used import is_uv_used
from usethis._integrations.ci.bitbucket.anchor import (
    ScriptItemAnchor as BitbucketScriptItemAnchor,
)
from usethis._integrations.ci.bitbucket.schema import Script as BitbucketScript
from usethis._integrations.ci.bitbucket.schema import Step as BitbucketStep
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.pre_commit.schema import HookDefinition, UriRepo
from usethis._tool.base import Tool
from usethis._tool.config import ConfigEntry, ConfigItem, ConfigSpec
from usethis._tool.pre_commit import PreCommitConfig
from usethis._types.deps import Dependency


class PyprojectFmtTool(Tool):
    # https://github.com/tox-dev/pyproject-fmt
    @property
    def name(self) -> str:
        return "pyproject-fmt"

    def print_how_to_use(self) -> None:
        install_method = self.get_install_method()
        if install_method == "pre-commit":
            if is_uv_used():
                box_print(
                    f"Run 'uv run pre-commit run pyproject-fmt --all-files' to run {self.name}."
                )
            else:
                box_print(
                    f"Run 'pre-commit run pyproject-fmt --all-files' to run {self.name}."
                )
        elif install_method == "devdep" or install_method is None:
            if is_uv_used():
                box_print(
                    f"Run 'uv run pyproject-fmt pyproject.toml' to run {self.name}."
                )
            else:
                box_print(f"Run 'pyproject-fmt pyproject.toml' to run {self.name}.")
        else:
            assert_never(install_method)

    def get_dev_deps(self, *, unconditional: bool = False) -> list[Dependency]:
        return [Dependency(name="pyproject-fmt")]

    def get_config_spec(self) -> ConfigSpec:
        # https://pyproject-fmt.readthedocs.io/en/latest/#configuration-via-file
        return ConfigSpec.from_flat(
            file_managers=[PyprojectTOMLManager()],
            resolution="first",
            config_items=[
                ConfigItem(
                    description="Overall Config",
                    root={
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "pyproject-fmt"]
                        )
                    },
                ),
                ConfigItem(
                    description="Keep Full Version",
                    root={
                        Path("pyproject.toml"): ConfigEntry(
                            keys=["tool", "pyproject-fmt", "keep_full_version"],
                            get_value=lambda: True,
                        )
                    },
                ),
            ],
        )

    def get_pre_commit_config(self) -> PreCommitConfig:
        return PreCommitConfig.from_single_repo(
            UriRepo(
                repo="https://github.com/tox-dev/pyproject-fmt",
                rev="v2.6.0",  # Manually bump this version when necessary
                hooks=[HookDefinition(id="pyproject-fmt")],
            ),
            requires_venv=False,
        )

    def get_bitbucket_steps(self) -> list[BitbucketStep]:
        return [
            BitbucketStep(
                name=f"Run {self.name}",
                caches=["uv"],
                script=BitbucketScript(
                    [
                        BitbucketScriptItemAnchor(name="install-uv"),
                        "uv run pyproject-fmt pyproject.toml",
                    ]
                ),
            )
        ]
