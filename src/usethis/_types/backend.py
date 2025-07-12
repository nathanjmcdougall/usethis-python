from enum import Enum


class BackendEnum(Enum):
    """Enumeration of available backends for usethis.

    "auto" doesn't represent an actual backend, but rather a mode where usethis
    automatically selects the backend based on the current environment or configuration.
    """

    auto = "auto"
    uv = "uv"
    none = "none"
