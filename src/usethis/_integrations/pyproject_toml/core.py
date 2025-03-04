from typing import Any

from usethis._integrations.pyproject_toml.errors import (
    PyprojectTOMLValueAlreadySetError,
    PyprojectTOMLValueMissingError,
)
from usethis._integrations.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.toml.core import (
    do_toml_id_keys_exist,
    extend_toml_list,
    get_toml_value,
    remove_from_toml_list,
    remove_toml_value,
    set_toml_value,
)
from usethis._integrations.toml.errors import (
    TOMLValueAlreadySetError,
    TOMLValueMissingError,
)


def get_pyproject_value(id_keys: list[str]) -> Any:
    pyproject = PyprojectTOMLManager().get()

    return get_toml_value(toml_document=pyproject, id_keys=id_keys)


def set_pyproject_value(
    id_keys: list[str], value: Any, *, exists_ok: bool = False
) -> None:
    """Set a value in the pyproject.toml configuration file."""
    pyproject = PyprojectTOMLManager().get()

    try:
        pyproject = set_toml_value(
            toml_document=pyproject, id_keys=id_keys, value=value, exists_ok=exists_ok
        )
    except TOMLValueAlreadySetError as err:
        raise PyprojectTOMLValueAlreadySetError(err) from None

    PyprojectTOMLManager().commit(pyproject)


def remove_pyproject_value(
    id_keys: list[str],
    *,
    missing_ok: bool = False,
) -> None:
    """Remove a value from the pyproject.toml configuration file."""
    pyproject = PyprojectTOMLManager().get()

    try:
        pyproject = remove_toml_value(toml_document=pyproject, id_keys=id_keys)
    except TOMLValueMissingError as err:
        if not missing_ok:
            raise PyprojectTOMLValueMissingError(err) from None
        # Otherwise, no changes are needed so skip the write step.
        return
    PyprojectTOMLManager().commit(pyproject)


def extend_pyproject_list(
    id_keys: list[str],
    values: list[Any],
) -> None:
    """Append values to a list in the pyproject.toml configuration file."""
    pyproject = PyprojectTOMLManager().get()

    pyproject = extend_toml_list(
        toml_document=pyproject,
        id_keys=id_keys,
        values=values,
    )

    PyprojectTOMLManager().commit(pyproject)


def remove_from_pyproject_list(id_keys: list[str], values: list[str]) -> None:
    pyproject = PyprojectTOMLManager().get()

    pyproject = remove_from_toml_list(
        toml_document=pyproject,
        id_keys=id_keys,
        values=values,
    )

    PyprojectTOMLManager().commit(pyproject)


def do_pyproject_id_keys_exist(id_keys: list[str]) -> bool:
    pyproject = PyprojectTOMLManager().get()

    return do_toml_id_keys_exist(
        toml_document=pyproject,
        id_keys=id_keys,
    )
