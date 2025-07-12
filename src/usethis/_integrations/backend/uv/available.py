from usethis._integrations.backend.uv.call import call_uv_subprocess
from usethis._integrations.backend.uv.errors import UVSubprocessFailedError


def is_uv_available() -> bool:
    """Check if the `uv` command is available in the current environment."""
    try:
        call_uv_subprocess(["--version"], change_toml=False)
    except UVSubprocessFailedError:
        return False

    return True
