from __future__ import annotations

import re

from usethis._integrations.backend.uv.call import call_uv_subprocess
from usethis._integrations.backend.uv.errors import UVUnparsedPythonVersionError
from usethis._integrations.file.pyproject_toml.requires_python import (
    MissingRequiresPythonError,
    get_requires_python,
)
from usethis._integrations.python.version import (
    extract_major_version,
    get_python_version,
)


def get_available_python_versions() -> set[str]:
    output = call_uv_subprocess(["python", "list", "--all-versions"], change_toml=False)

    return {
        _parse_python_version_from_uv_output(version) for version in output.splitlines()
    }


def get_supported_major_python_versions() -> list[int]:
    try:
        requires_python = get_requires_python()
    except MissingRequiresPythonError:
        return [extract_major_version(get_python_version())]

    versions = set()
    for version in get_available_python_versions():
        # N.B. a standard range won't include alpha versions.
        if requires_python.contains(version):
            versions.add(version)

    return sorted({extract_major_version(version) for version in versions})


def _parse_python_version_from_uv_output(version: str) -> str:
    match = re.match(r"^[A-Za-z]*-(\d{1,2}.\d{1,2}.\d{1,2}[a-z\d]*)+[+-].*$", version)

    if match:
        return match.group(1)
    else:
        msg = f"Could not parse version from '{version}'."
        raise UVUnparsedPythonVersionError(msg)


def python_pin(version: str) -> None:
    call_uv_subprocess(["python", "pin", version], change_toml=False)
