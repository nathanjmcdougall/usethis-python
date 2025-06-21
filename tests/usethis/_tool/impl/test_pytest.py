from pathlib import Path
from sysconfig import get_python_version

import pytest


class TestPytestTool:
    class TestUpdateBitbucketSteps:
        def test_new_file(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
            # Arrange
            from usethis._config_file import files_manager
            from usethis._integrations.ci.bitbucket.steps import (
                add_placeholder_step_in_default,
            )
            from usethis._test import change_cwd
            from usethis._tool.impl.pytest import PytestTool

            with change_cwd(uv_init_dir), files_manager():
                add_placeholder_step_in_default(report_placeholder=False)
                (uv_init_dir / "pytest.ini").touch()

                # Act
                PytestTool().update_bitbucket_steps()

            # Assert
            assert (uv_init_dir / "bitbucket-pipelines.yml").exists()
            contents = (uv_init_dir / "bitbucket-pipelines.yml").read_text()
            assert (
                contents
                == """\
image: atlassian/default-image:3
definitions:
    caches:
        uv: ~/.cache/uv
    script_items:
      - &install-uv |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.local/bin/env
        export UV_LINK_MODE=copy
        uv --version
pipelines:
    default:
      - step:
            name: Test on 3.12
            caches:
              - uv
            script:
              - *install-uv
              - uv run --python 3.12 pytest -x --junitxml=test-reports/report.xml
      - step:
            name: Test on 3.13
            caches:
              - uv
            script:
              - *install-uv
              - uv run --python 3.13 pytest -x --junitxml=test-reports/report.xml
"""
            )

            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Writing 'bitbucket-pipelines.yml'.\n"
                "✔ Adding cache 'uv' definition to 'bitbucket-pipelines.yml'.\n"
                "✔ Adding 'Test on 3.12' to default pipeline in 'bitbucket-pipelines.yml'.\n"
                "✔ Adding 'Test on 3.13' to default pipeline in 'bitbucket-pipelines.yml'.\n"
            )

        def test_remove_old_steps(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            """Note this test also checks we don't add a cache when it's not needed."""
            # Arrange
            from usethis._config_file import files_manager
            from usethis._test import change_cwd
            from usethis._tool.impl.pytest import PytestTool

            (uv_init_dir / "bitbucket-pipelines.yml").write_text(
                """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Test on 3.11
            script:
              - echo 'Hello, Python 3.11!'
      - step:
            name: Test on 3.12
            script:
              - echo 'Hello, Python 3.12!'
"""
            )
            (uv_init_dir / "pyproject.toml").write_text(
                """\
[project]
requires-python = ">=3.12,<3.13"
version = "0.1.0"
"""
            )
            (uv_init_dir / "pytest.ini").touch()

            # Act
            with change_cwd(uv_init_dir), files_manager():
                PytestTool().update_bitbucket_steps()

            # Assert
            contents = (uv_init_dir / "bitbucket-pipelines.yml").read_text()
            assert (
                contents
                == """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Test on 3.12
            script:
              - echo 'Hello, Python 3.12!'
"""
            )
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Removing 'Test on 3.11' from default pipeline in 'bitbucket-pipelines.yml'.\n"
            )

        def test_no_requires_python(self, tmp_path: Path):
            # Arrange
            from usethis._config_file import files_manager
            from usethis._integrations.ci.bitbucket.steps import (
                add_placeholder_step_in_default,
            )
            from usethis._integrations.python.version import extract_major_version
            from usethis._test import change_cwd
            from usethis._tool.impl.pytest import PytestTool

            (tmp_path / "pyproject.toml").write_text(
                """\
[project]
name = "example"
version = "0.1.0"
"""
            )
            (tmp_path / "pytest.ini").touch()

            with change_cwd(tmp_path), files_manager():
                add_placeholder_step_in_default(report_placeholder=False)

                # Act
                PytestTool().update_bitbucket_steps()

            # Assert
            contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
            version = extract_major_version(get_python_version())
            assert (
                contents
                == f"""\
image: atlassian/default-image:3
definitions:
    caches:
        uv: ~/.cache/uv
    script_items:
      - &install-uv |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.local/bin/env
        export UV_LINK_MODE=copy
        uv --version
pipelines:
    default:
      - step:
            name: Test on 3.{version}
            caches:
              - uv
            script:
              - *install-uv
              - uv run --python 3.{version} pytest -x --junitxml=test-reports/report.xml
"""
            )

    class TestRemoveBitbucketSteps:
        def test_no_file(self, uv_init_dir: Path):
            # Arrange
            from usethis._test import change_cwd
            from usethis._tool.impl.pytest import PytestTool

            # Act
            with change_cwd(uv_init_dir):
                PytestTool().remove_bitbucket_steps()

            # Assert
            assert not (uv_init_dir / "bitbucket-pipelines.yml").exists()

        def test_dont_touch_if_no_pytest_steps(self, uv_init_dir: Path):
            # Arrange
            from usethis._config_file import files_manager
            from usethis._integrations.ci.bitbucket.steps import (
                add_placeholder_step_in_default,
            )
            from usethis._test import change_cwd
            from usethis._tool.impl.pytest import PytestTool

            with change_cwd(uv_init_dir), files_manager():
                add_placeholder_step_in_default(report_placeholder=False)
                PytestTool().update_bitbucket_steps()
            contents = (uv_init_dir / "bitbucket-pipelines.yml").read_text()
            (uv_init_dir / "pytest.ini").touch()

            # Act
            with change_cwd(uv_init_dir), files_manager():
                PytestTool().remove_bitbucket_steps()

            # Assert
            assert (uv_init_dir / "bitbucket-pipelines.yml").exists()
            assert (uv_init_dir / "bitbucket-pipelines.yml").read_text() == contents

        def test_one_step(self, uv_init_dir: Path):
            # Arrange
            from usethis._integrations.file.pyproject_toml.io_ import (
                PyprojectTOMLManager,
            )
            from usethis._test import change_cwd
            from usethis._tool.impl.pytest import PytestTool

            (uv_init_dir / "bitbucket-pipelines.yml").write_text(
                """\
image: atlassian/default-image:3
pipelines:
  default:
    - step:
        name: Test on 3.12
        script:
          - echo 'Hello, Python 3.12!'
"""
            )

            # Act
            with change_cwd(uv_init_dir), PyprojectTOMLManager():
                PytestTool().remove_bitbucket_steps()

            # Assert
            contents = (uv_init_dir / "bitbucket-pipelines.yml").read_text()
            assert (
                contents
                == """\
image: atlassian/default-image:3
definitions:
    caches:
        uv: ~/.cache/uv
    script_items:
      - &install-uv |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.local/bin/env
        export UV_LINK_MODE=copy
        uv --version
pipelines:
    default:
      - step:
            name: Placeholder - add your own steps!
            caches:
              - uv
            script:
              - *install-uv
              - echo 'Hello, world!'
"""
            )
