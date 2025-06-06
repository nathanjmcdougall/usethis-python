from usethis._config import (
    frozen_opt,
    how_opt,
    offline_opt,
    quiet_opt,
    remove_opt,
    usethis_config,
)
from usethis._config_file import files_manager
from usethis._core.tool import use_deptry, use_ruff


def lint(
    remove: bool = remove_opt,
    how: bool = how_opt,
    offline: bool = offline_opt,
    quiet: bool = quiet_opt,
    frozen: bool = frozen_opt,
) -> None:
    """Add recommended linters to the project."""
    with (
        usethis_config.set(offline=offline, quiet=quiet, frozen=frozen),
        files_manager(),
    ):
        use_ruff(linter=True, formatter=False, remove=remove, how=how)
        use_deptry(remove=remove, how=how)
