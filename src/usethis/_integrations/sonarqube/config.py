from __future__ import annotations

import re
from pathlib import Path

from pydantic import TypeAdapter

from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.project.layout import get_source_dir_str
from usethis._integrations.python.version import get_python_version
from usethis._integrations.sonarqube.errors import (
    CoverageReportConfigNotFoundError,
    InvalidSonarQubeProjectKeyError,
    MissingProjectKeyError,
)


class _NonstandardPythonVersionError(Exception):
    """Raised when a non-standard Python version is detected."""


def get_sonar_project_properties() -> str:
    """Get contents for (or from) the sonar-project.properties file."""
    path = Path.cwd() / "sonar-project.properties"
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8")

    try:
        python_version = _get_short_version(Path(".python-version").read_text().strip())
    except (FileNotFoundError, _NonstandardPythonVersionError):
        python_version = get_python_version()

    try:
        project_key = PyprojectTOMLManager()[
            ["tool", "usethis", "sonarqube", "project-key"]
        ]
    except (FileNotFoundError, KeyError):
        msg = "Could not find SonarQube project key at 'tool.usethis.sonarqube.project-key' in 'pyproject.toml'."
        raise MissingProjectKeyError(msg) from None
    _validate_project_key(project_key)

    try:
        verbose = PyprojectTOMLManager()[["tool", "usethis", "sonarqube", "verbose"]]
    except (FileNotFoundError, KeyError):
        verbose = False
    verbose = TypeAdapter(bool).validate_python(verbose)

    try:
        exclusions = PyprojectTOMLManager()[
            ["tool", "usethis", "sonarqube", "exclusions"]
        ]
    except (FileNotFoundError, KeyError):
        exclusions = []
    exclusions = TypeAdapter(list).validate_python(exclusions)
    for exclusion in exclusions:
        TypeAdapter(str).validate_python(exclusion)

    try:
        coverage_output = PyprojectTOMLManager()[["tool", "coverage", "xml", "output"]]
    except (FileNotFoundError, KeyError):
        msg = "XML coverage report file path not found at 'tool.coverage.xml.output' in 'pyproject.toml'."
        raise CoverageReportConfigNotFoundError(msg) from None

    # No file, so construct the contents
    source_dir_str = get_source_dir_str()
    if source_dir_str == ".":
        sources = "./"
    else:
        sources = f"./{source_dir_str}"

    text = f"""\
sonar.projectKey={project_key}
sonar.language=py
sonar.python.version={python_version}
sonar.sources={sources}
sonar.tests=./tests
sonar.python.coverage.reportPaths={coverage_output}
sonar.verbose={"true" if verbose else "false"}
"""
    if exclusions:
        text += "sonar.exclusions=" + ", ".join(exclusions) + "\n"
    return text


def _get_short_version(version: str) -> str:
    match = re.match(r"^(\d+\.\d+)", version)
    if match is None:
        msg = f"Could not parse Python version from {version}"
        raise _NonstandardPythonVersionError(msg)

    return match.group(1)


def _validate_project_key(project_key: str) -> None:
    """Validate the SonarQube project key.

    The key must contain at least one non-digit character.
    Allowed characters are:
    a through z,
    A through Z,
    - (dash),
    _ (underscore),
    . (dot),
    : (colon)
    and the digits 0 through 9.

    This value is case-sensitive.
    """
    _RE = r"^[a-zA-Z0-9\-_:.]+$"
    if re.match(_RE, project_key) is None or project_key.isdigit():
        msg = f"Invalid SonarQube project key: {project_key}"
        raise InvalidSonarQubeProjectKeyError(msg)
