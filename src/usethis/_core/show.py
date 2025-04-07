from __future__ import annotations

from usethis._config import usethis_config
from usethis._integrations.project.name import get_project_name
from usethis._integrations.sonarqube.config import get_sonar_project_properties
from usethis._integrations.uv.init import ensure_pyproject_toml


def show_name() -> None:
    print(get_project_name())


def show_sonarqube_config() -> None:
    with usethis_config.set(quiet=True):
        ensure_pyproject_toml()
    get_sonar_project_properties()
