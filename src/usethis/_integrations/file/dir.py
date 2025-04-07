from pathlib import Path


def get_project_name_from_dir() -> str:
    # Use the name of the parent directory
    # Names must start and end with a letter or digit and may only contain -, _, ., and
    # alphanumeric characters. Any other characters will be dropped. If there are no
    # valid characters, the name will be "my_project".
    # https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#name
    dir_name = Path.cwd().name
    name = "".join(c for c in dir_name if c.isalnum() or c in {"-", "_", "."})
    if not name:
        name = "my_project"

    return name
