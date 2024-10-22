from pathlib import Path

import typer

from usethis._bitbucket.config import (
    add_bitbucket_pipeline_config,
    remove_bitbucket_pipeline_config,
)
from usethis._bitbucket.steps import Step, StepRef, add_steps
from usethis._pyproject.requires_python import get_supported_major_python_versions
from usethis._tool import PreCommitTool, PytestTool

app = typer.Typer(help="Add config for Continuous Integration (CI) pipelines.")


@app.command(help="Use Bitbucket pipelines for CI.")
def bitbucket(
    remove: bool = typer.Option(
        False, "--remove", help="Remove Bitbucket pipelines CI instead of adding it."
    ),
) -> None:
    _bitbucket(remove=remove)


def _bitbucket(*, remove: bool = False) -> None:
    config_yaml_path = Path.cwd() / "bitbucket-pipelines.yml"

    if config_yaml_path.exists():
        if remove:
            remove_bitbucket_pipeline_config()
        else:
            # Early exit; the file already exists so we will leave it alone.
            return

    add_bitbucket_pipeline_config()

    steps = []
    if PreCommitTool().is_used():
        steps.append(
            Step(
                name="Run pre-commit hooks",
                caches=["uv", "pre-commit"],
                script=[
                    StepRef(name="install-uv"),
                    "uv run pre-commit run --all-files",
                ],
            )
        )
    if PytestTool().is_used():
        matrix = get_supported_major_python_versions()
        for version in matrix:
            steps.append(
                Step(
                    name=f"Run tests with Python 3.{version}",
                    caches=["uv"],
                    script=[
                        StepRef(name="install-uv"),
                        f"uv run --python 3.{version} pytest",
                    ],
                )
            )

    if not steps:
        # Add a dummy step
        steps.append(
            Step(
                name="Placeholder - add your own steps!",
                caches=[],
                script=[StepRef(name="install-uv"), "echo 'Hello, world!'"],
            )
        )

    add_steps(steps, is_parallel=True)