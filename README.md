<h1 align="center">
  <img src="https://raw.githubusercontent.com/usethis-python/usethis-python/refs/heads/main/docs/logo.svg"><br>
</h1>

# usethis

[![usethis](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/usethis-python/usethis-python/main/assets/badge/v1.json)](https://github.com/usethis-python/usethis-python)
[![PyPI Version](https://img.shields.io/pypi/v/usethis.svg)](https://pypi.python.org/pypi/usethis)
![PyPI License](https://img.shields.io/pypi/l/usethis.svg)
[![PyPI Supported Versions](https://img.shields.io/pypi/pyversions/usethis.svg)](https://pypi.python.org/pypi/usethis)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![CodSpeed](https://img.shields.io/endpoint?url=https://codspeed.io/badge.json)](https://codspeed.io/usethis-python/usethis-python)
[![codecov](https://codecov.io/gh/usethis-python/usethis-python/graph/badge.svg?token=MU1AZS0KHV)](https://codecov.io/gh/usethis-python/usethis-python)
[![GitHub Actions Status](https://github.com/usethis-python/usethis-python/workflows/CI/badge.svg)](https://github.com/usethis-python/usethis-python/actions)

Automate Python project setup and development tasks that are otherwise performed manually.

usethis knows about popular Python tools, workflows and frameworks, and knows how they interact. It can declaratively add and remove tools, configure them, and set up the project for you. It does this all in a way that won't break your existing configuration and will make the necessary adjustments to your project configuration files.

usethis gives detailed messages about what it is doing (and what you need to do next).

- Output beginning with `✔` represents a task which usethis has automated.
- Output beginning with `☐` represents a task which you need to perform manually.
- Output beginning with `ℹ` gives hints and tips.

Inspired by an [**R** package of the same name](https://usethis.r-lib.org/index.html), this package brings a similar experience to the Python ecosystem as a CLI tool.

## Highlights

- 🧰 First-class support for state-of-the-practice tooling: uv, Ruff, pytest, pre-commit, and many more.
- 🤖 Automatically add and remove tools: declare, install, and configure in one step.
- 🧠 Powerful knowledge of how different tools interact and sensible defaults.
- 🔄 Update existing configuration files automatically.
- 📢 Fully declarative project configuration.
- ⚡ Get started on a new Python project or a new workflow in seconds.

## 🧭 Getting Started

First, it is strongly recommended you [install the uv package manager](https://docs.astral.sh/uv/getting-started/installation/): this is a simple, documented process. If you're already using uv, make sure you're using at least
version v0.5.29 (run `uv version` to check, and `uv self update` to upgrade).

You can install usethis directly into the project environment:

```console
# With uv
$ uv add --dev usethis

# With pip
$ pip install usethis
```

Alternatively, you can also run usethis commands in isolation, using `uvx` or `pipx`. For example, to add Ruff to the project:

```console
# With uv
$ uvx usethis tool ruff

# With pipx
$ pipx run usethis tool ruff
```

## 🖥️ Command Line Interface

### Start a New Project

- [`usethis init`](#usethis-init) — Initialize a new project with recommended defaults.

### Manage Tooling

- [`usethis format`](#usethis-format) — Add/Configure recommended formatters (namely, [Ruff](https://docs.astral.sh/ruff/formatter/) and [pyproject-fmt](https://pyproject-fmt.readthedocs.io/en/latest/)).
- [`usethis lint`](#usethis-lint) — Add/Configure recommended linters (namely, [Ruff](https://docs.astral.sh/ruff/linter) and [deptry](https://github.com/fpgmaas/deptry)).
- [`usethis spellcheck`](#usethis-spellcheck) — Add/Configure recommended spellcheckers (namely, [codespell](https://github.com/codespell-project/codespell)).
- [`usethis test`](#usethis-test) — Add/Configure a recommended testing framework (namely, [pytest](https://github.com/pytest-dev/pytest)).
- [`usethis ci`](#usethis-ci) — Add/Configure a recommended CI service.
- [`usethis tool`](#usethis-tool) — Add/Configure specific tools individually.

### Manage Configuration

- [`usethis author`](#usethis-author) — Set new author information for the project.
- [`usethis docstyle`](#usethis-docstyle-style) — Set new author information for the project.
- [`usethis rule`](#usethis-rule-rulecode) — Set a docstring style convention for the project, and [enforce it with Ruff](https://docs.astral.sh/ruff/rules/#pydocstyle-d).
- [`usethis status`](#usethis-status-status) — Set the development status of the project (via trove classifiers).

### Manage README

- [`usethis badge`](#usethis-badge) — Set new author information for the project.
- [`usethis readme`](#usethis-readme) — Add badges to the README file.

### Information

- [`usethis list`](#usethis-list) — Display a table of all available tools and their current usage status.
- [`usethis version`](#usethis-version) — Display the current version of usethis.
- [`usethis browse pypi`](#usethis-browse-pypi-package) — Display or open the PyPI landing page associated with another project.
- [`usethis show`](#usethis-show) — Show a specific piece of information about the project.

## 💡 Example Usage

To start a new project from scratch with a complete set of recommended tooling, run:

```console
$ uvx usethis init
✔ Writing 'pyproject.toml' and initializing project.
✔ Writing 'README.md'.
☐ Populate 'README.md' to help users understand the project.
✔ Adding recommended linters.
☐ Run 'uv run ruff check --fix' to run the Ruff linter with autofixes.
☐ Run 'uv run deptry src' to run deptry.
✔ Adding recommended formatters.
☐ Run 'uv run ruff format' to run the Ruff formatter.
☐ Run 'uv run pyproject-fmt pyproject.toml' to run pyproject-fmt.
✔ Adding recommended spellcheckers.
☐ Run 'uv run codespell' to run the Codespell spellchecker.
✔ Adding recommended test frameworks.
☐ Add test files to the '/tests' directory with the format 'test_*.py'.
☐ Add test functions with the format 'test_*()'.
☐ Run 'uv run pytest' to run the tests.
☐ Run 'uv run pytest --cov' to run your tests with Coverage.py.
```

To use Ruff on an existing project, run:

```console
$ uvx usethis tool ruff
✔ Adding dependency 'ruff' to the 'dev' group in 'pyproject.toml'.
✔ Adding Ruff config to 'pyproject.toml'.
✔ Selecting Ruff rules 'A', 'C4', 'E4', 'E7', 'E9', 'F', 'FLY', 'FURB', 'I', 'PLE', 'PLR', 'RUF', 'SIM', 'UP' in 'pyproject.toml'.
✔ Ignoring Ruff rules 'PLR2004', 'SIM108' in 'pyproject.toml'.
☐ Run 'uv run ruff check --fix' to run the Ruff linter with autofixes.
☐ Run 'uv run ruff format' to run the Ruff formatter.
```

To use pytest, run:

```console
$ uvx usethis tool pytest
✔ Adding dependency 'pytest' to the 'test' group in 'pyproject.toml'.
✔ Adding pytest config to 'pyproject.toml'.
✔ Selecting Ruff rule 'PT' in 'pyproject.toml'.
✔ Creating '/tests'.
✔ Writing '/tests/conftest.py'.
☐ Add test files to the '/tests' directory with the format 'test_*.py'.
☐ Add test functions with the format 'test_*()'.
☐ Run 'uv run pytest' to run the tests.
```

To configure Bitbucket pipelines, run:

```console
$ uvx usethis ci bitbucket
✔ Writing 'bitbucket-pipelines.yml'.
✔ Adding cache 'uv' definition to 'bitbucket-pipelines.yml'.
✔ Adding 'Run Ruff' to default pipeline in 'bitbucket-pipelines.yml'.
✔ Adding 'Test on 3.12' to default pipeline in 'bitbucket-pipelines.yml'.
✔ Adding 'Test on 3.13' to default pipeline in 'bitbucket-pipelines.yml'.
☐ Run your pipeline via the Bitbucket website.
```

## 🖥️ Command Reference

### `usethis init`

Initialize a new Python project with recommended defaults, including:

- a `pyproject.toml` file and relevant configuration,
- recommended linters, formatters, spellcheckers, and test frameworks (all opt-out),
- docstring style enforcement (opt-in),
- the pre-commit framework (opt-in),
- CI services (opt-in),
- declared & installed dependencies via `uv add`, and
- any other relevant directories or tool-bespoke configuration files.

Supported options:

- `--format` to add recommended formatters (default; or `--no-format` to opt-out)
- `--lint` to add recommended linters (default; or `--no-lint` to opt-out)
- `--spellcheck` to add a recommended spellchecker (default; or `--no-spellcheck` to opt-out)
- `--test` to add a recommended testing framework (default; or `--no-test` to opt-out)
- `--pre-commit` to add the pre-commit framework for git hooks (but the default is `--no-pre-commit`)
- `--ci` to add a CI service configuration
  Possible values:
  - `bitbucket` for [Bitbucket Pipelines](https://bitbucket.org/product/features/pipelines)
- `--docstyle` to set a docstring style convention for the project
  Possible values:
  - `numpy` for [NumPy docstring style](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard)
  - `google` for [Google docstring style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
  - `pep257` for [PEP 257 docstring style](https://www.python.org/dev/peps/pep-0257/)
- `--status` to set the development status of the project. Defaults to `planning`.
  Possible values:
  - `planning` or `1` for "Development Status :: 1 - Planning"
  - `pre-alpha` or `2` for "Development Status :: 2 - Pre-Alpha"
  - `alpha` or `3` for "Development Status :: 3 - Alpha"
  - `beta` or `4` for "Development Status :: 4 - Beta"
  - `production` or `5` for "Development Status :: 5 - Production/Stable"
  - `mature` or `6` for "Development Status :: 6 - Mature"
  - `inactive` or `7` for "Development Status :: 7 - Inactive"
- `--offline` to disable network access and rely on caches
- `--quiet` to suppress output
- `--frozen` to leave the virtual environment and lockfile unchanged (i.e. do not install dependencies, nor update lockfiles)
- `--backend` to specify a package manager backend to use. The default is to auto-detect.
Possible values:
  - `auto` to auto-detect the backend (default)
  - `uv` to use the [uv](https://docs.astral.sh/uv) package manager
  - `none` to not use a package manager backend and display messages for some operations.

### `usethis format`

Add recommended formatters to the project (namely, [Ruff](https://docs.astral.sh/ruff/formatter/) and [pyproject-fmt](https://pyproject-fmt.readthedocs.io/en/latest/)), including:

- declared & installed dependencies via `uv add`,
- relevant `pyproject.toml` configuration, and
- any other relevant directories or tool-bespoke configuration files.

Note if `pyproject.toml` is not present, it will be created, since this is required for declaring dependencies via `uv add`.

Supported options:

- `--remove` to remove the tool instead of adding it
- `--how` to only print how to use the tool, with no other side effects
- `--offline` to disable network access and rely on caches
- `--frozen` to leave the virtual environment and lockfile unchanged
- `--quiet` to suppress output
- `--backend` to specify a package manager backend to use. The default is to auto-detect.
Possible values:
  - `auto` to auto-detect the backend (default)
  - `uv` to use the [uv](https://docs.astral.sh/uv) package manager
  - `none` to not use a package manager backend and display messages for some operations.

See [`usethis tool`](#usethis-tool) for more information.

### `usethis lint`

Add recommended linters to the project (namely, [Ruff](https://docs.astral.sh/ruff/linter) and [deptry](https://github.com/fpgmaas/deptry)), including:

- declared & installed dependencies with `uv add`,
- relevant `pyproject.toml` configuration, and
- any other relevant directories or tool-bespoke configuration files.

Note if `pyproject.toml` is not present, it will be created, since this is required for declaring dependencies with `uv add`.

Supported options:

- `--remove` to remove the tool instead of adding it
- `--how` to only print how to use the tool, with no other side effects
- `--offline` to disable network access and rely on caches
- `--frozen` to leave the virtual environment and lockfile unchanged
- `--quiet` to suppress output
- `--backend` to specify a package manager backend to use. The default is to auto-detect.
Possible values:
  - `auto` to auto-detect the backend (default)
  - `uv` to use the [uv](https://docs.astral.sh/uv) package manager
  - `none` to not use a package manager backend and display messages for some operations.

See [`usethis tool`](#usethis-tool) for more information.

### `usethis spellcheck`

Add a recommended spellchecker to the project (namely, [codespell](https://github.com/codespell-project/codespell)), including:

- declared & installed dependencies with `uv add`,
- relevant `pyproject.toml` configuration, and
- any other relevant directories or tool-bespoke configuration files.

Note if `pyproject.toml` is not present, it will be created, since this is required for declaring dependencies with `uv add`.

Supported options:

- `--remove` to remove the tool instead of adding it
- `--how` to only print how to use the tool, with no other side effects
- `--offline` to disable network access and rely on caches
- `--frozen` to leave the virtual environment and lockfile unchanged
- `--quiet` to suppress output
- `--backend` to specify a package manager backend to use. The default is to auto-detect.
Possible values:
  - `auto` to auto-detect the backend (default)
  - `uv` to use the [uv](https://docs.astral.sh/uv) package manager
  - `none` to not use a package manager backend and display messages for some operations.

See [`usethis tool`](#usethis-tool) for more information.

### `usethis test`

Add a recommended testing framework to the project (namely pytest), including:

- declared & installed dependencies with `uv add`,
- relevant `pyproject.toml` configuration, and
- any other relevant directories or tool-bespoke configuration files.

Note if `pyproject.toml` is not present, it will be created, since this is required for declaring dependencies with `uv add`.

Supported options:

- `--remove` to remove the tool instead of adding it
- `--how` to only print how to use the tool, with no other side effects
- `--offline` to disable network access and rely on caches
- `--frozen` to leave the virtual environment and lockfile unchanged
- `--quiet` to suppress output
- `--backend` to specify a package manager backend to use. The default is to auto-detect.
Possible values:
  - `auto` to auto-detect the backend (default)
  - `uv` to use the [uv](https://docs.astral.sh/uv) package manager
  - `none` to not use a package manager backend and display messages for some operations.

See [`usethis tool`](#usethis-tool) for more information.

### `usethis tool`

Add a new tool to a Python project, including:

- declared & installed dependencies with `uv add`,
- relevant `pyproject.toml` configuration,
- any other relevant directories or tool-bespoke configuration files, and
- `.pre-commit-config.yaml` configuration if using `pre-commit`.

Note if `pyproject.toml` is not present, it will be created, since this is required for
declaring dependencies with `uv add`.

#### Code Quality Tools

- `usethis tool codespell` - Use the [codespell spellchecker](https://github.com/codespell-project/codespell): detect common spelling mistakes.
- `usethis tool deptry` - Use the [deptry linter](https://github.com/fpgmaas/deptry): avoid missing or superfluous dependency declarations.
- `usethis tool import-linter` - Use [Import Linter](https://import-linter.readthedocs.io/en/stable/): enforce a self-imposed architecture on imports.
- `usethis tool pre-commit` - Use the [pre-commit](https://github.com/pre-commit/pre-commit) framework to manage and maintain pre-commit hooks.
- `usethis tool pyproject-fmt` - Use the [pyproject-fmt linter](https://github.com/tox-dev/pyproject-fmt): opinionated formatting of 'pyproject.toml' files.
- `usethis tool ruff` - Use [Ruff](https://github.com/astral-sh/ruff): an extremely fast Python linter and code formatter.

#### Testing

- `usethis tool coverage.py` - Use [Coverage.py](https://github.com/nedbat/coveragepy): a code coverage measurement tool.
- `usethis tool pytest` - Use the [pytest](https://github.com/pytest-dev/pytest) testing framework.

#### Configuration Files

- `usethis tool pyproject.toml` - Use a [pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#writing-your-pyproject-toml) file to configure the project.
- `usethis tool requirements.txt` - Use a [requirements.txt](https://pip.pypa.io/en/stable/reference/requirements-file-format/) file exported from the uv lockfile.

Supported options:

- `--remove` to remove the tool instead of adding it
- `--how` to only print how to use the tool, with no other side effects
- `--offline` to disable network access and rely on caches
- `--frozen` to leave the virtual environment and lockfile unchanged
- `--quiet` to suppress output
- `--backend` to specify a package manager backend to use. The default is to auto-detect.
Possible values:
  - `auto` to auto-detect the backend (default)
  - `uv` to use the [uv](https://docs.astral.sh/uv) package manager
  - `none` to not use a package manager backend and display messages for some operations.

For `usethis tool ruff`, in addition to the above options, you can also specify:

- `--linter` to add or remove specifically the linter component of Ruff (default; or `--no-linter` to opt-out)
- `--formatter` to add or remove specifically the formatter component of Ruff (default; or `--no-formatter` to opt-out)

### `usethis ci`

Add Continuous Integration pipelines to the project.

Currently supported platforms:

- `usethis ci bitbcuket` - Use [Bitbucket Pipelines](https://bitbucket.org/product/features/pipelines): a CI/CD service for Bitbucket.

Supported options:

- `--remove` to remove the CI configuration instead of adding it
- `--offline` to disable network access and rely on caches
- `--quiet` to suppress output
- `--frozen` to leave the virtual environment and lockfile unchanged (i.e. do not install dependencies, nor update lockfiles)
- `--backend` to specify a package manager backend to use. The default is to auto-detect.
Possible values:
  - `auto` to auto-detect the backend (default)
  - `uv` to use the [uv](https://docs.astral.sh/uv) package manager
  - `none` to not use a package manager backend and display messages for some operations.

### `usethis badge`

Add badges to the README file.

Currently supported badges:

- `usethis badge pre-commit` - [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
- `usethis badge pypi` - [![PyPI Version](https://img.shields.io/pypi/v/usethis.svg)](https://pypi.python.org/pypi/usethis)
- `usethis badge ruff` - [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
- `usethis badge usethis` - [![usethis](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/usethis-python/usethis-python/main/assets/badge/v1.json)](https://github.com/usethis-python/usethis-python)
- `usethis badge uv` - [![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

Supported options:

- `--show` to show the badge URL instead of adding (or removing) it
- `--remove` to remove the badge instead of adding it
- `--offline` to disable network access and rely on caches
- `--quiet` to suppress output

### `usethis readme`

Add a README.md file to the project.

Supported options:

- `--badges` to also add badges to the README.md file
- `--quiet` to suppress output
- `--backend` to specify a package manager backend to use. The default is to auto-detect.
Possible values:
  - `auto` to auto-detect the backend (default)
  - `uv` to use the [uv](https://docs.astral.sh/uv) package manager
  - `none` to not use a package manager backend and display messages for some operations.

### `usethis author`

Set new author information for the project.

Required options:

- `--name` for the new author's name

Other supported options:

- `--email` to set the author email address
- `--overwrite` to overwrite all existing author information
- `--quiet` to suppress output
- `--backend` to specify a package manager backend to use. The default is to auto-detect.
Possible values:
  - `auto` to auto-detect the backend (default)
  - `uv` to use the [uv](https://docs.astral.sh/uv) package manager
  - `none` to not use a package manager backend and display messages for some operations.

### `usethis docstyle <style>`

Set a docstring style convention for the project, and [enforce it with Ruff](https://docs.astral.sh/ruff/rules/#pydocstyle-d).

Defaults to the Google docstring style.

Possible style options:

- `numpy` for [NumPy docstring style](https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard)
- `google` for [Google docstring style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- `pep257` for [PEP 257 docstring style](https://www.python.org/dev/peps/pep-0257/)

Example:

`usethis docstyle google`

Supported options:

- `--offline` to disable network access and rely on caches
- `--quiet` to suppress output
- `--frozen` to leave the virtual environment and lockfile unchanged (i.e. do not install dependencies, nor update lockfiles)
- `--backend` to specify a package manager backend to use. The default is to auto-detect.
Possible values:
  - `auto` to auto-detect the backend (default)
  - `uv` to use the [uv](https://docs.astral.sh/uv) package manager
  - `none` to not use a package manager backend and display messages for some operations.

### `usethis rule <rulecode>`

Add (or manage configuration) of Ruff and Deptry rules in `pyproject.toml`.

See [the Ruff documentation](https://docs.astral.sh/ruff/rules/) for a list of available
rules, and [the Deptry documentation](https://deptry.com/rules-violations/) for a list
of available rules.

Example:

`usethis rule RUF001`

Supported options:

- `--remove` to remove the rule selection or ignore status.
- `--ignore` to add the rule to the ignore list (or remove it if --remove is specified).
- `--offline` to disable network access and rely on caches
- `--quiet` to suppress output
- `--backend` to specify a package manager backend to use. The default is to auto-detect.
Possible values:
  - `auto` to auto-detect the backend (default)
  - `uv` to use the [uv](https://docs.astral.sh/uv) package manager
  - `none` to not use a package manager backend and display messages for some operations.

### `usethis status <status>`

Set the development status of the project via trove classifiers.

Possible values (required):

- `usethis status planning` or `usethis status 1` for "Development Status :: 1 - Planning"
- `usethis status pre-alpha` or `usethis status 2` for "Development Status :: 2 - Pre-Alpha"
- `usethis status alpha` or `usethis status 3` for "Development Status :: 3 - Alpha"
- `usethis status beta` or `usethis status 4` for "Development Status :: 4 - Beta"
- `usethis status production` or `usethis status 5` for "Development Status :: 5 - Production/Stable"
- `usethis status mature` or `usethis status 6` for "Development Status :: 6 - Mature"
- `usethis status inactive` or `usethis status 7` for "Development Status :: 7 - Inactive"

Supported options:

- `--badges` to add an associated badge to the README file
- `--quiet` to suppress output

### `usethis list`

Display a table of all available tools and their current usage status.

### `usethis version`

Display the current version of usethis.

### `usethis show`

Show a piece of information about the project.

Currently supported subcommands:

- `usethis show name` to show the name of the project.
- `usethis show sonarqube` to show appropriate contents of a `sonar-projects.properties` file for SonarQube analysis.

### `usethis browse pypi <package>`

Display or open the PyPI landing page associated with another project.

Example:

`usethis browse pypi numpy`

Supported options:

- `--browser` to open the link in the browser automatically.

## 📚 Similar Projects

Not sure if usethis is the exact fit for your project?

The closest match to usethis is [PyScaffold](https://github.com/pyscaffold/pyscaffold/). It provides a Command Line Interface to automate the creation of a project from a sensible templated structure.

You could also consider your own hard-coded template. Templating tools such as [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and [Copier](https://github.com/copier-org/copier) allow you to create static templates with fixed configuration you can use across multiple projects. However, it's not always obvious which template you should use, and many do not use state-of-practice tooling such as `pyproject.toml`. Also, sometimes a template can overwhelm you with too many unfamiliar tools.

You could consider [this template](https://github.com/pawamoy/copier-uv) or [this one](https://github.com/jlevy/simple-modern-uv), which work with Copier, or [this template](https://github.com/johnthagen/python-blueprint) which works with Cookiecutter.

> [!TIP]
> You can still use usethis as a part of a templates using [hooks](https://cookiecutter.readthedocs.io/en/latest/advanced/hooks.html#using-pre-post-generate-hooks-0-7-0) for Cookiecutter and [tasks](https://copier.readthedocs.io/en/stable/configuring/#tasks) for Copier.

If you're using Cookiecutter, then you can update to a latest version of a template using a tool like [cruft](https://github.com/cruft/cruft). Copier has inbuilt support for template updating. Another template-style option which provides updating is [jaraco/skeleton](https://blog.jaraco.com/skeleton/), which is a specific, git-based template rather than a general templating system.

## 🚀 Development

[![Commits since latest release](https://img.shields.io/github/commits-since/usethis-python/usethis-python/latest.svg)](https://github.com/usethis-python/usethis-python/releases)

### Roadmap

Major features planned for later in 2025 are:

- Support for automated GitHub Actions workflows ([#57](https://github.com/usethis-python/usethis-python/issues/57)),
- Support for a typechecker (likely Pyright, [#121](https://github.com/usethis-python/usethis-python/issues/121)), and
- Support for documentation pages (likely using mkdocs, [#188](https://github.com/usethis-python/usethis-python/issues/188)).

Other features are tracked in the [GitHub Issues](https://github.com/usethis-python/usethis-python/issues) page.

### Contributing

See the
[CONTRIBUTING.md](https://github.com/usethis-python/usethis-python/blob/main/CONTRIBUTING.md)
file.

## License

usethis is licensed under the MIT license ([LICENSE](https://github.com/usethis-python/usethis-python/blob/main/LICENSE) or <https://opensource.org/licenses/MIT>)

Unless you explicitly state otherwise, any contribution intentionally submitted for inclusion in usethis by you, as defined in the Apache License, Version 2.0, (<https://www.apache.org/licenses/LICENSE-2.0>), shall be licensed under the MIT license, without any additional terms or conditions.
