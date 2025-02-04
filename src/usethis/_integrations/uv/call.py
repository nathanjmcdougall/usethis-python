from usethis._integrations.pyproject.io_ import read_pyproject_toml_from_path
from usethis._integrations.uv.errors import UVSubprocessFailedError
from usethis._subprocess import SubprocessFailedError, call_subprocess
from usethis._config import usethis_config

def call_uv_subprocess(args: list[str]) -> str:
    """Run a subprocess using the uv command-line tool.

    Raises:
        UVSubprocessFailedError: If the subprocess fails.
    """
    read_pyproject_toml_from_path.cache_clear()
    try:
        if usethis_config.frozen:
            args.append("--frozen")
            return call_subprocess(["uv", *args], check=False)
        return call_subprocess(["uv", *args])
    except SubprocessFailedError as err:
        raise UVSubprocessFailedError(err) from None
