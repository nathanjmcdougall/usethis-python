from usethis._config import usethis_config
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager


def is_uv_used() -> bool:
    return (
        (usethis_config.cpd() / "uv.lock").exists()
        or (usethis_config.cpd() / "uv.toml").exists()
        or ["tool", "uv"] in PyprojectTOMLManager()
    )
