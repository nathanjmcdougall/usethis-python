# Contributing

Thank you for your interest in contributing to usethis! There are issues labeled
[Good First Issue](https://github.com/usethis-python/usethis-python/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22good%20first%20issue%22)
which are good opportunities for new contributors.

Since `usethis` is at early stages of development, please
[ensure a GitHub Issue is opened](https://github.com/usethis-python/usethis-python/issues)
before starting work on a new feature or bug fix. This helps to ensure that the
feature is aligned with the project's goals and that there is no duplication of effort. Sometimes these Issues don't have enough guidance in them, so consider asking for some more guidance from the ticket creator before getting started.

## Setup

### Development Environment

[uv](https://github.com/astral-sh/uv) is required to install the development
environment. You can install it using the instructions here:

<https://docs.astral.sh/uv/getting-started/installation/>

Then with the current working directory set to the project root, run:

```shell
uv sync
```

### Pre-commit Hooks

This project uses the `pre-commit` framework to manage Git hooks. To install the hooks,
run:

```shell
uv run pre-commit install
```

## Testing

### Running the Test Suite

To run the tests, simply run:

```shell
uv run pytest
```

### Writing Tests

Tests are written using the `pytest` framework. The test suite is located in the
`tests` directory. The tests are organized into subdirectories with a directory
structure that mirrors the structure of the code being tested. This makes it easy
to find the tests for a specific module or function.

PRs should ideally include tests for any new features or bug fixes.

## Documentation

Documentation is hosted at <https://usethis.readthedocs.io/en/latest/>. It can be served
locally with:

```shell
uv run mkdocs serve
```

Docstrings use Google Style.

## Version Control

Git is used for version control, using
[Trunk-based development](https://trunkbaseddevelopment.com/).

It is recommended that you use signed commits, although this is not a requirement.
Please see this guide from the VS Code project for instructions on how to do this:
<https://github.com/microsoft/vscode/wiki/Commit-Signing>

## Architecture

This project uses [Import Linter](https://import-linter.readthedocs.io/en/stable/) to
enforce a software architecture. Refer to the `[[tool.importlinter.contracts]]` sections
in `pyproject.toml` to understand the structure of the project.

## Conventions

### Print statements

To ensure the `--quiet` flag is always effective, avoid using simple `print` statements.
Instead, use the purpose-built `usethis._console.plain_print` function.
