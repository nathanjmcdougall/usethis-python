# Security Policy

## Scope of security vulnerabilities

usethis invokes other software on the system, specifically [uv](https://github.com/astral-sh/uv/blob/main/SECURITY.md). This can execute arbitrary code due to the inherent nature of the Python ecosystem and the way that uv is designed. It is the user's responsibility to ensure that the correct uv executable lies on `PATH` under the command `uv`.

The test suite also invokes [Git](https://git-scm.com/). It is your responsibility to ensure that the correct Git executable lies on `PATH` under the command `git`.

These are not considered vulnerabilities in usethis.

## Reporting a vulnerability

Please use the [GitHub vulnerability reporting form](https://github.com/usethis-python/usethis-python/security/advisories/new) to report a vulnerability.
