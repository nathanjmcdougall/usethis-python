from pathlib import Path

import pytest


class TestAddBitbucketStepInDefault:
    def test_contents(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            add_bitbucket_step_in_default,
        )
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        (uv_init_dir / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            script: ["echo 'Hello, world!'"]
"""
        )

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_bitbucket_step_in_default(
                Step(
                    name="Greeting",
                    script=Script(["echo 'Why, hello!'"]),
                ),
            )

        # Assert
        with open(uv_init_dir / "bitbucket-pipelines.yml") as f:
            contents = f.read()
        assert (
            # N.B. the step is added as soon as possible, i.e. at the top of the pipeline
            contents
            == """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Greeting
            script:
              - echo 'Why, hello!'
      - step:
            script: ["echo 'Hello, world!'"]
"""
        )

    def test_pipeline_doesnt_exist(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            add_bitbucket_step_in_default,
        )
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        (uv_init_dir / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines: {}
"""
        )

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_bitbucket_step_in_default(
                Step(
                    name="Greeting",
                    script=Script(["echo 'Hello, world!'"]),
                )
            )

        # Assert
        contents = (uv_init_dir / "bitbucket-pipelines.yml").read_text()
        assert (
            contents
            == """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Greeting
            script:
              - echo 'Hello, world!'
"""
        )

    def test_with_caches(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            add_bitbucket_step_in_default,
        )
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        (uv_init_dir / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines: {}
"""
        )

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_bitbucket_step_in_default(
                Step(
                    name="Greeting",
                    caches=["uv"],
                    script=Script(["echo 'Hello, world!'"]),
                )
            )

        # Assert
        contents = (uv_init_dir / "bitbucket-pipelines.yml").read_text()
        assert (
            contents
            == """\
image: atlassian/default-image:3
definitions:
    caches:
        uv: ~/.cache/uv
pipelines:
    default:
      - step:
            name: Greeting
            caches:
              - uv
            script:
              - echo 'Hello, world!'
"""
        )

    def test_add_same_step_twice(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.anchor import ScriptItemAnchor
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            add_bitbucket_step_in_default,
        )
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        step = Step(
            name="Greeting",
            script=Script(
                [
                    ScriptItemAnchor(name="install-uv"),
                    "echo 'Hello, world!'",
                ]
            ),
        )

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_bitbucket_step_in_default(step)

            contents = (uv_init_dir / "bitbucket-pipelines.yml").read_text()

            # Act
            add_bitbucket_step_in_default(step)

        # Assert
        assert contents == (uv_init_dir / "bitbucket-pipelines.yml").read_text()

    def test_add_different_steps_sharing_same_script_step_anchor(
        self, uv_init_dir: Path
    ):
        # Arrange
        from usethis._integrations.ci.bitbucket.anchor import ScriptItemAnchor
        from usethis._integrations.ci.bitbucket.io_ import edit_bitbucket_pipelines_yaml
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            add_bitbucket_step_in_default,
            get_defined_script_items_via_doc,
        )
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        step = Step(
            name="Greeting",
            script=Script(
                [
                    ScriptItemAnchor(name="install-uv"),
                    "echo 'Hello, world!'",
                ]
            ),
        )
        other_step = Step(
            name="Farewell",
            script=Script(
                [
                    ScriptItemAnchor(name="install-uv"),
                    "echo 'Goodbye!'",
                ]
            ),
        )

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            # Act
            add_bitbucket_step_in_default(step)
            add_bitbucket_step_in_default(other_step)

            # Assert
            with edit_bitbucket_pipelines_yaml() as doc:
                item_by_name = get_defined_script_items_via_doc(doc=doc)
                assert len(item_by_name) == 1

    def test_order(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            add_bitbucket_step_in_default,
        )
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            # This step should be listed second
            add_bitbucket_step_in_default(
                Step(
                    name="Test on 3.12",
                    script=Script(["echo 'Running #2'"]),
                ),
            )
            # This one should come first
            add_bitbucket_step_in_default(
                Step(
                    name="Run pre-commit",
                    script=Script(["echo 'Running #1'"]),
                ),
            )

        # Assert
        with open(uv_init_dir / "bitbucket-pipelines.yml") as f:
            contents = f.read()
        assert (
            contents
            == """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Run pre-commit
            script:
              - "echo 'Running #1'"
      - step:
            name: Test on 3.12
            script:
              - "echo 'Running #2'"
"""
        )
        out, err = capfd.readouterr()
        assert out == (
            "✔ Writing 'bitbucket-pipelines.yml'.\n"
            "✔ Adding 'Test on 3.12' to default pipeline in 'bitbucket-pipelines.yml'.\n"
            "✔ Adding 'Run pre-commit' to default pipeline in 'bitbucket-pipelines.yml'.\n"
        )

    def test_placeholder_removed(
        self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
    ):
        # Arrange
        from usethis._config import usethis_config
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            add_bitbucket_step_in_default,
            add_placeholder_step_in_default,
        )
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            with usethis_config.set(quiet=True):
                add_placeholder_step_in_default()

            # Act
            add_bitbucket_step_in_default(
                Step(
                    name="Greeting",
                    script=Script(["echo 'Hello, world!'"]),
                )
            )

            # Assert
            with open(uv_init_dir / "bitbucket-pipelines.yml") as f:
                contents = f.read()

            assert (
                contents
                == """\
image: atlassian/default-image:3
definitions:
    script_items:
      - &install-uv |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.local/bin/env
        export UV_LINK_MODE=copy
        uv --version
pipelines:
    default:
      - step:
            name: Greeting
            script:
              - echo 'Hello, world!'
"""
            )
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Adding 'Greeting' to default pipeline in 'bitbucket-pipelines.yml'.\n"
                "✔ Removing cache 'uv' definition from 'bitbucket-pipelines.yml'.\n"
            )

    def test_add_script_item_to_existing_file(
        self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
    ):
        # Arrange
        from usethis._integrations.ci.bitbucket.anchor import ScriptItemAnchor
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            add_bitbucket_step_in_default,
        )
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        (uv_init_dir / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
definitions:
    script_items:
      - &install-uv |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.local/bin/env
        export UV_LINK_MODE=copy
        uv --version
pipelines:
    default:
      - step:
            name: Greeting
            script:
              - *install-uv
              - echo 'Hello, world!'
"""
        )

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_bitbucket_step_in_default(
                Step(
                    name="Farewell",
                    script=Script(
                        [
                            ScriptItemAnchor(name="install-uv"),
                            "echo 'Goodbye!'",
                        ]
                    ),
                )
            )

        # Assert
        contents = (uv_init_dir / "bitbucket-pipelines.yml").read_text()
        assert (
            contents
            == """\
image: atlassian/default-image:3
definitions:
    script_items:
      - &install-uv |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.local/bin/env
        export UV_LINK_MODE=copy
        uv --version
pipelines:
    default:
      - step:
            name: Farewell
            script:
              - *install-uv
              - echo 'Goodbye!'
      - step:
            name: Greeting
            script:
              - *install-uv
              - echo 'Hello, world!'
"""
        )
        out, err = capfd.readouterr()
        assert out == (
            "✔ Adding 'Farewell' to default pipeline in 'bitbucket-pipelines.yml'.\n"
        )
        assert not err


class TestRemoveBitbucketStepFromDefault:
    def test_remove_remove_one_step(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            remove_bitbucket_step_from_default,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Greeting
            script: 
                - echo 'Hello, world!'
      - step:
            name: Farewell
            script:
                - echo 'Goodbye!'
"""
        )

        # Act
        with change_cwd(tmp_path):
            remove_bitbucket_step_from_default(
                Step(
                    name="Greeting",
                    script=Script(["echo 'Hello, world!'"]),
                )
            )

        # Assert
        contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert (
            contents
            == """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Farewell
            script:
              - echo 'Goodbye!'
"""
        )

    def test_no_file(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            remove_bitbucket_step_from_default,
        )
        from usethis._test import change_cwd

        # Act
        with change_cwd(tmp_path):
            remove_bitbucket_step_from_default(
                Step(
                    name="Greeting",
                    script=Script(["echo 'Hello, world!'"]),
                )
            )

        # Assert
        assert not (tmp_path / "bitbucket-pipelines.yml").exists()

    def test_no_default_pipeline(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            remove_bitbucket_step_from_default,
        )
        from usethis._test import change_cwd

        txt = """\
image: atlassian/default-image:3
pipelines: {}
"""
        (tmp_path / "bitbucket-pipelines.yml").write_text(txt)

        # Act
        with change_cwd(tmp_path):
            remove_bitbucket_step_from_default(
                Step(
                    name="Greeting",
                    script=Script(["echo 'Hello, world!'"]),
                )
            )

        # Assert
        assert (tmp_path / "bitbucket-pipelines.yml").read_text() == txt

    def test_no_pipelines(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            remove_bitbucket_step_from_default,
        )
        from usethis._test import change_cwd

        txt = """\
image: atlassian/default-image:3
"""
        (tmp_path / "bitbucket-pipelines.yml").write_text(txt)

        # Act
        with change_cwd(tmp_path):
            remove_bitbucket_step_from_default(
                Step(
                    name="Greeting",
                    script=Script(["echo 'Hello, world!'"]),
                )
            )

        # Assert
        assert (tmp_path / "bitbucket-pipelines.yml").read_text() == txt

    def test_import_pipeline_fails(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            UnexpectedImportPipelineError,
            remove_bitbucket_step_from_default,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines:
    default:
        import: shared-pipeline:master:share-pipeline-1
"""
        )

        # Act, Assert
        with change_cwd(tmp_path), pytest.raises(UnexpectedImportPipelineError):
            remove_bitbucket_step_from_default(
                Step(
                    name="Greeting",
                    script=Script(["echo 'Hello, world!'"]),
                )
            )

    def test_parallel_item(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            remove_bitbucket_step_from_default,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines:
    default:
      - parallel:
          - step:
                name: Greeting
                script:
                  - echo 'Hello, world!'
          - step:
                name: Farewell
                script:
                    - echo 'Goodbye!'
"""
        )

        # Act
        with change_cwd(tmp_path):
            remove_bitbucket_step_from_default(
                Step(
                    name="Greeting",
                    script=Script(["echo 'Hello, world!'"]),
                )
            )

        # Assert
        contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert (
            contents
            == """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Farewell
            script:
              - echo 'Goodbye!'
"""
        )

    def test_remove_single_parallel_step(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            remove_bitbucket_step_from_default,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines:
    default:
      - parallel:
            - step:
                name: Greeting
                script:
                    - echo 'Hello, world!'
      - step:
            name: Farewell
            script:
              - echo 'Goodbye!'
"""
        )

        # Act
        with change_cwd(tmp_path):
            remove_bitbucket_step_from_default(
                Step(
                    name="Greeting",
                    script=Script(["echo 'Hello, world!"]),
                )
            )

        # Assert
        contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert (
            contents
            == """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Farewell
            script:
              - echo 'Goodbye!'
"""
        )

    def test_remove_leaving_single_parallel_step(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            remove_bitbucket_step_from_default,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines:
    default:
      - parallel:
            - step:
                name: Greeting
                script:
                    - echo 'Hello, world!'
      - step:
            name: Farewell
            script:
              - echo 'Goodbye!'
"""
        )

        # Act
        with change_cwd(tmp_path):
            remove_bitbucket_step_from_default(
                Step(
                    name="Farewell",
                    script=Script(["echo 'Goodbye!'"]),
                )
            )

        # Assert
        contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert (
            contents
            == """\
image: atlassian/default-image:3
pipelines:
    default:
      - parallel:
          - step:
                name: Greeting
                script:
                  - echo 'Hello, world!'
"""
        )

    def test_remove_step_leaving_placeholder(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            remove_bitbucket_step_from_default,
        )
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        (uv_init_dir / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Farewell
            script:
              - echo 'Goodbye!'
"""
        )

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            remove_bitbucket_step_from_default(
                Step(
                    name="Farewell",
                    script=Script(["echo 'Goodbye!'"]),
                )
            )

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

    def test_remove_expanded_parallel_step(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            remove_bitbucket_step_from_default,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines:
    default:
      - parallel:
            failfast: true
            steps:
              - step:
                    name: Greeting
                    script:
                        - echo 'Hello, world!'
              - step:
                    name: Farewell
                    script:
                      - echo 'Goodbye!'
"""
        )

        # Act
        with change_cwd(tmp_path):
            remove_bitbucket_step_from_default(
                Step(
                    name="Greeting",
                    script=Script(["echo 'Hello, world!'"]),
                )
            )

        # Assert
        contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert (
            contents
            == """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Farewell
            script:
              - echo 'Goodbye!'
"""
        )

    def test_remove_leaving_single_expanded_parallel_step(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            remove_bitbucket_step_from_default,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines:
    default:
      - parallel:
            fail-fast: true
            steps:
              - step:
                    name: Greeting
                    script:
                      - echo 'Hello, world!'
      - step:
            name: Farewell
            script:
              - echo 'Goodbye!'
"""
        )

        # Act
        with change_cwd(tmp_path):
            remove_bitbucket_step_from_default(
                Step(
                    name="Farewell",
                    script=Script(["echo 'Goodbye!'"]),
                )
            )

        # Assert
        contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert (
            contents
            == """\
image: atlassian/default-image:3
pipelines:
    default:
      - parallel:
            fail-fast: true
            steps:
              - step:
                    name: Greeting
                    script:
                      - echo 'Hello, world!'
"""
        )

    def test_stage_item(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            remove_bitbucket_step_from_default,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Greeting
            script:
              - echo 'Hello, world!'
      - stage:
            name: Farewell
            steps:
              - step:
                    name: Farewell
                    script:
                      - echo 'Goodbye!'  
              - step:
                    name: Well wishes
                    script:
                      - echo 'Be well!'  
"""
        )

        # Act
        with change_cwd(tmp_path):
            remove_bitbucket_step_from_default(
                Step(
                    name="Farewell",
                    script=Script(["echo 'Goodbye!'"]),
                )
            )

        # Assert
        contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert (
            contents
            == """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Greeting
            script:
              - echo 'Hello, world!'
      - stage:
            name: Farewell
            steps:
              - step:
                    name: Well wishes
                    script:
                      - echo 'Be well!'
"""
        )

    def test_remove_stage_item_leaving_placeholder(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            remove_bitbucket_step_from_default,
        )
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        (uv_init_dir / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines:
    default:
      - stage:
            name: Farewell
            steps:
              - step:
                    name: Farewell
                    script:
                      - echo 'Goodbye!'
"""
        )

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            remove_bitbucket_step_from_default(
                Step(
                    name="Farewell",
                    script=Script(["echo 'Goodbye!'"]),
                )
            )

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


class TestGetStepsInPipelineItem:
    class TestStepItem:
        def test_step(self):
            # Arrange
            from usethis._integrations.ci.bitbucket.schema import Script, StepItem
            from usethis._integrations.ci.bitbucket.steps import (
                Step,
                get_steps_in_pipeline_item,
            )

            step = Step(script=Script(["echo 'Hello, world!'"]))
            item = StepItem(step=step)

            # Act
            steps = get_steps_in_pipeline_item(item)

            # Assert
            assert steps == [step]

    class TestParallelItem:
        def test_parallel_steps(self):
            # Arrange
            from usethis._integrations.ci.bitbucket.schema import (
                Parallel,
                ParallelItem,
                ParallelSteps,
                Script,
                StepItem,
            )
            from usethis._integrations.ci.bitbucket.steps import (
                Step,
                get_steps_in_pipeline_item,
            )

            original_steps = [
                Step(script=Script(["echo 'Hello, world!'"])),
                Step(script=Script(["echo 'Why, hello!'"])),
            ]
            item = ParallelItem(
                parallel=Parallel(
                    ParallelSteps([StepItem(step=step) for step in original_steps])
                )
            )

            # Act
            steps = get_steps_in_pipeline_item(item)

            # Assert
            assert steps == original_steps

        def test_parallel_expanded(self):
            # Arrange
            from usethis._integrations.ci.bitbucket.schema import (
                Parallel,
                ParallelExpanded,
                ParallelItem,
                ParallelSteps,
                Script,
                StepItem,
            )
            from usethis._integrations.ci.bitbucket.steps import (
                Step,
                get_steps_in_pipeline_item,
            )

            original_steps = [
                Step(script=Script(["echo 'Hello, world!'"])),
                Step(script=Script(["echo 'Why, hello!'"])),
            ]
            item = ParallelItem(
                parallel=Parallel(
                    ParallelExpanded(
                        steps=ParallelSteps(
                            [StepItem(step=step) for step in original_steps]
                        )
                    )
                )
            )

            # Act
            steps = get_steps_in_pipeline_item(item)

            # Assert
            assert steps == original_steps

    class TestStageItem:
        def test_steps(self):
            # Arrange
            from usethis._integrations.ci.bitbucket.schema import (
                Script,
                Stage,
                StageItem,
                Step1,
                Step2,
            )
            from usethis._integrations.ci.bitbucket.steps import (
                Step,
                get_steps_in_pipeline_item,
            )

            script = Script(["echo 'Hello, world!'"])
            item = StageItem(
                stage=Stage(
                    steps=[
                        Step1(
                            step=Step2(
                                name="greetings",
                                script=Script(["echo 'Hello, world!'"]),
                            )
                        ),
                    ]
                )
            )

            # Act
            steps = get_steps_in_pipeline_item(item)

            # Assert
            assert steps == [Step(name="greetings", script=script)]


class TestAddPlaceholderStepInDefault:
    EXPECTED_YML_SIMPLE_PLACEHOLDER = """\
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

    def test_contents(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._integrations.ci.bitbucket.steps import (
            add_placeholder_step_in_default,
        )
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_placeholder_step_in_default()

        # Assert
        assert (uv_init_dir / "bitbucket-pipelines.yml").exists()
        assert (
            uv_init_dir / "bitbucket-pipelines.yml"
        ).read_text() == self.EXPECTED_YML_SIMPLE_PLACEHOLDER

        out, _ = capfd.readouterr()
        # Keep these messages in sync with the ones used for pre-commit
        assert out == (
            "✔ Writing 'bitbucket-pipelines.yml'.\n"
            "✔ Adding cache 'uv' definition to 'bitbucket-pipelines.yml'.\n"
            "✔ Adding placeholder step to default pipeline in 'bitbucket-pipelines.yml'.\n"
            "☐ Remove the placeholder pipeline step in 'bitbucket-pipelines.yml'.\n"
            "☐ Replace it with your own pipeline steps.\n"
            "☐ Alternatively, use 'usethis tool' to add other tools and their steps.\n"
        )

    def test_idempotent(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.steps import (
            add_placeholder_step_in_default,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            self.EXPECTED_YML_SIMPLE_PLACEHOLDER
        )

        # Act
        with change_cwd(tmp_path):
            add_placeholder_step_in_default()

        # Assert
        assert (
            tmp_path / "bitbucket-pipelines.yml"
        ).read_text() == self.EXPECTED_YML_SIMPLE_PLACEHOLDER


class TestGetDefinedScriptItemNames:
    def test_empty(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.io_ import edit_bitbucket_pipelines_yaml
        from usethis._integrations.ci.bitbucket.steps import (
            get_defined_script_items_via_doc,
        )
        from usethis._test import change_cwd

        # Act
        with change_cwd(tmp_path), edit_bitbucket_pipelines_yaml() as doc:
            item_by_name = get_defined_script_items_via_doc(doc=doc)

        # Assert
        assert item_by_name == {}

    def test_no_definitions_section(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.io_ import edit_bitbucket_pipelines_yaml
        from usethis._integrations.ci.bitbucket.steps import (
            get_defined_script_items_via_doc,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
"""
        )

        # Act
        with change_cwd(tmp_path), edit_bitbucket_pipelines_yaml() as doc:
            item_by_name = get_defined_script_items_via_doc(doc=doc)

        # Assert
        assert item_by_name == {}

    def test_no_script_items_definitions_section(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.io_ import edit_bitbucket_pipelines_yaml
        from usethis._integrations.ci.bitbucket.steps import (
            get_defined_script_items_via_doc,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
definitions:
    caches:
        uv: ~/.cache/uv
"""
        )

        # Act
        with change_cwd(tmp_path), edit_bitbucket_pipelines_yaml() as doc:
            item_by_name = get_defined_script_items_via_doc(doc=doc)

        # Assert
        assert item_by_name == {}

    def test_no_anchor(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.io_ import edit_bitbucket_pipelines_yaml
        from usethis._integrations.ci.bitbucket.steps import (
            get_defined_script_items_via_doc,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
definitions:
    script_items:
      - echo 'Hello, world!'
"""
        )

        # Act
        with change_cwd(tmp_path), edit_bitbucket_pipelines_yaml() as doc:
            item_by_name = get_defined_script_items_via_doc(doc=doc)

        # Assert
        assert item_by_name == {}

    def test_anchor(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.io_ import edit_bitbucket_pipelines_yaml
        from usethis._integrations.ci.bitbucket.steps import (
            get_defined_script_items_via_doc,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
definitions:
    script_items:
      - &say-hello |
        echo 'Hello, world!'
"""
        )

        # Act
        with change_cwd(tmp_path), edit_bitbucket_pipelines_yaml() as doc:
            item_by_name = get_defined_script_items_via_doc(doc=doc)

        # Assert
        assert list(item_by_name.keys()) == ["say-hello"]

    def test_multiline_no_anchor(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.io_ import edit_bitbucket_pipelines_yaml
        from usethis._integrations.ci.bitbucket.steps import (
            get_defined_script_items_via_doc,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
definitions:
    script_items:
      - |
        echo 'Hello, world!'
"""
        )

        # Act
        with change_cwd(tmp_path), edit_bitbucket_pipelines_yaml() as doc:
            item_by_name = get_defined_script_items_via_doc(doc=doc)

        # Assert
        assert item_by_name == {}


class TestAddStepCachesViaDoc:
    def test_unrecognized(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.io_ import edit_bitbucket_pipelines_yaml
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            _CACHE_LOOKUP,
            Step,
            _add_step_caches_via_doc,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
"""
        )

        # Act, Assert
        assert set(_CACHE_LOOKUP.keys()) == {"uv", "pre-commit"}
        match = (
            "Unrecognized cache name 'unrecognized' in step 'Greeting'. "
            "Supported caches are 'uv' and 'pre-commit'."
        )
        with (
            change_cwd(tmp_path),
            pytest.raises(NotImplementedError, match=match),
            edit_bitbucket_pipelines_yaml() as doc,
        ):
            _add_step_caches_via_doc(
                step=Step(
                    name="Greeting",
                    caches=["unrecognized"],
                    script=Script(["echo 'Hello, world!'"]),
                ),
                doc=doc,
            )


class TestStepsAreEquivalent:
    def test_identical(self):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            bitbucket_steps_are_equivalent,
        )

        step = Step(
            name="Greeting",
            script=Script(["echo 'Hello, world!'"]),
        )
        other = Step(
            name="Greeting",
            script=Script(["echo 'Hello, world!'"]),
        )

        # Act
        result = bitbucket_steps_are_equivalent(step, other)

        # Assert
        assert result is True

    def test_different_name(self):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            bitbucket_steps_are_equivalent,
        )

        step = Step(
            name="Greeting",
            script=Script(["echo 'Hello, world!'"]),
        )
        other = Step(
            name="Farewell",
            script=Script(["echo 'Hello, world!'"]),
        )

        # Act
        result = bitbucket_steps_are_equivalent(step, other)

        # Assert
        assert result is True

    def test_different_script(self):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            bitbucket_steps_are_equivalent,
        )

        step = Step(
            name="Greeting",
            script=Script(["echo 'Hello, world!'"]),
        )
        other = Step(
            name="Greeting",
            script=Script(["echo 'Goodbye!'"]),
        )

        # Act
        result = bitbucket_steps_are_equivalent(step, other)

        # Assert
        assert result is True

    def test_case_sensitive_name_difference(self):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            bitbucket_steps_are_equivalent,
        )

        step = Step(
            name="Greeting",
            script=Script(["echo 'Hello, world!'"]),
        )
        other = Step(
            name="greeting",
            script=Script(["echo 'See ya!'"]),
        )

        # Act
        result = bitbucket_steps_are_equivalent(step, other)

        # Assert
        assert result is True

    def test_none(self):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            bitbucket_steps_are_equivalent,
        )

        step = None
        other = Step(
            name="Greeting",
            script=Script(["echo 'Hello, world!'"]),
        )

        # Act
        result = bitbucket_steps_are_equivalent(step, other)

        # Assert
        assert result is False


class TestGetStepsInDefault:
    def test_no_file(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.steps import get_steps_in_default
        from usethis._test import change_cwd

        # Act
        with change_cwd(tmp_path):
            steps = get_steps_in_default()

        # Assert
        assert steps == []

    def test_no_pipelines(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.steps import get_steps_in_default
        from usethis._test import change_cwd

        content = """\
image: atlassian/default-image:3
"""
        (tmp_path / "bitbucket-pipelines.yml").write_text(content)

        # Act
        with change_cwd(tmp_path):
            steps = get_steps_in_default()

        # Assert
        assert steps == []

    def test_no_default_pipeline(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.steps import get_steps_in_default
        from usethis._test import change_cwd

        content = """\
image: atlassian/default-image:3
pipelines: {}
"""
        (tmp_path / "bitbucket-pipelines.yml").write_text(content)

        # Act
        with change_cwd(tmp_path):
            steps = get_steps_in_default()

        # Assert
        assert steps == []

    def test_other_pipelines_not_default(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.steps import get_steps_in_default
        from usethis._test import change_cwd

        content = """\
image: atlassian/default-image:3
pipelines:
    branches:
        master:
            - step:
                  name: Greeting
                  script:
                    - echo 'Hello, world!'
"""
        (tmp_path / "bitbucket-pipelines.yml").write_text(content)

        # Act
        with change_cwd(tmp_path):
            steps = get_steps_in_default()

        # Assert
        assert steps == []

    def test_default_pipeline(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.schema import Script
        from usethis._integrations.ci.bitbucket.steps import Step, get_steps_in_default
        from usethis._test import change_cwd

        content = """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            name: Greeting
            script:
              - echo 'Hello, world!'
"""
        (tmp_path / "bitbucket-pipelines.yml").write_text(content)

        # Act
        with change_cwd(tmp_path):
            steps = get_steps_in_default()

        # Assert
        assert steps == [
            Step(
                name="Greeting",
                script=Script(["echo 'Hello, world!'"]),
            )
        ]

    def test_import_pipeline(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.steps import (
            UnexpectedImportPipelineError,
            get_steps_in_default,
        )
        from usethis._test import change_cwd

        content = """\
image: atlassian/default-image:3
pipelines:
    default:
        import: shared-pipeline:master:share-pipeline-1
"""
        (tmp_path / "bitbucket-pipelines.yml").write_text(content)

        # Act, Assert
        with change_cwd(tmp_path), pytest.raises(UnexpectedImportPipelineError):
            get_steps_in_default()
