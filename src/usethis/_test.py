from __future__ import annotations

import os
import socket
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator


@contextmanager
def change_cwd(new_dir: Path) -> Generator[None, None, None]:
    """Change the working directory temporarily.

    Arguments:
        new_dir: The new directory to change to.
    """
    old_dir = Path.cwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(old_dir)


def is_offline() -> bool:
    try:
        # Connect to Google's DNS server
        s = socket.create_connection(("8.8.8.8", 53), timeout=3)
    except OSError:
        return True
    else:
        s.close()
        return False
