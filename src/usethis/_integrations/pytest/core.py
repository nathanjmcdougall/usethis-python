import shutil
from pathlib import Path

from usethis._console import console


def add_pytest_dir() -> None:
    tests_dir = Path.cwd() / "tests"

    if not tests_dir.exists():
        console.tick_print("Creating '/tests'.")
        tests_dir.mkdir()

    if (tests_dir / "conftest.py").exists():
        # Early exit; conftest.py already exists
        return

    console.tick_print("Writing '/tests/conftest.py'.")
    (tests_dir / "conftest.py").write_text(
        "collect_ignore_glob = []\npytest_plugins = []\n"
    )


def remove_pytest_dir() -> None:
    tests_dir = Path.cwd() / "tests"

    if not tests_dir.exists():
        # Early exit; tests directory does not exist
        return

    if set(tests_dir.iterdir()) <= {tests_dir / "conftest.py"}:
        # The only file in the directory is conftest.py
        console.tick_print("Removing '/tests'.")
        shutil.rmtree(tests_dir)
    else:
        console.box_print("Reconfigure the /tests directory to run without pytest.")
        # Note we don't actually remove the directory, just explain what needs to be done.