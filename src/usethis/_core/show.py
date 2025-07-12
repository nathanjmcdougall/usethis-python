from __future__ import annotations

from usethis._config import usethis_config
from usethis._console import plain_print
from usethis._integrations.backend.uv.init import ensure_pyproject_toml
from usethis._integrations.project.name import get_project_name
from usethis._integrations.sonarqube.config import get_sonar_project_properties


def show_name() -> None:
    plain_print(get_project_name())


def show_sonarqube_config() -> None:
    with usethis_config.set(quiet=True):
        ensure_pyproject_toml()
    plain_print(get_sonar_project_properties())
