from __future__ import annotations

from usethis._console import tick_print
from usethis._integrations.backend.uv.init import ensure_pyproject_toml
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._types.status import DevelopmentStatusEnum


def use_development_status(
    status: DevelopmentStatusEnum,
) -> None:
    ensure_pyproject_toml()

    new_classifier = _STATUS_TO_CLASSIFIER_MAP[status]

    dispstatus = new_classifier.removeprefix("Development Status :: ")

    tick_print(f"Setting the development status to '{dispstatus}'.")

    mgr = PyprojectTOMLManager()
    try:
        existing_classifiers = mgr[["project", "classifiers"]]
    except KeyError:
        existing_classifiers = []
    existing_status_classifiers = {
        classifier
        for classifier in existing_classifiers
        if classifier in STATUS_CLASSIFIERS
    }
    mgr.remove_from_list(
        keys=["project", "classifiers"],
        values=existing_status_classifiers,
    )

    mgr.extend_list(
        keys=["project", "classifiers"],
        values=[new_classifier],
    )


_STATUS_TO_CLASSIFIER_MAP = {
    DevelopmentStatusEnum.planning: "Development Status :: 1 - Planning",
    DevelopmentStatusEnum.planning_code: "Development Status :: 1 - Planning",
    DevelopmentStatusEnum.prealpha: "Development Status :: 2 - Pre-Alpha",
    DevelopmentStatusEnum.prealpha_code: "Development Status :: 2 - Pre-Alpha",
    DevelopmentStatusEnum.alpha: "Development Status :: 3 - Alpha",
    DevelopmentStatusEnum.alpha_code: "Development Status :: 3 - Alpha",
    DevelopmentStatusEnum.beta: "Development Status :: 4 - Beta",
    DevelopmentStatusEnum.beta_code: "Development Status :: 4 - Beta",
    DevelopmentStatusEnum.production: "Development Status :: 5 - Production/Stable",
    DevelopmentStatusEnum.production_code: "Development Status :: 5 - Production/Stable",
    DevelopmentStatusEnum.mature: "Development Status :: 6 - Mature",
    DevelopmentStatusEnum.mature_code: "Development Status :: 6 - Mature",
    DevelopmentStatusEnum.inactive: "Development Status :: 7 - Inactive",
    DevelopmentStatusEnum.inactive_code: "Development Status :: 7 - Inactive",
}

STATUS_CLASSIFIERS = set(_STATUS_TO_CLASSIFIER_MAP.values())
