from pathlib import Path


class TestAddBitbucketPipelineConfig:
    def test_blank_slate(self, uv_init_dir: Path):
        from usethis._integrations.ci.bitbucket.config import (
            add_bitbucket_pipeline_config,
        )
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_bitbucket_pipeline_config()

        assert (uv_init_dir / "bitbucket-pipelines.yml").exists()
        content = (uv_init_dir / "bitbucket-pipelines.yml").read_text()
        assert content == (
            """\
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

    def test_existing_file(self, tmp_path: Path):
        from usethis._integrations.ci.bitbucket.config import (
            add_bitbucket_pipeline_config,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text("existing content")

        with change_cwd(tmp_path):
            add_bitbucket_pipeline_config()

        assert (tmp_path / "bitbucket-pipelines.yml").exists()
        content = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert content == "existing content"

    def test_satisfies_schema(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.anchor import ScriptItemAnchor
        from usethis._integrations.ci.bitbucket.config import (
            add_bitbucket_pipeline_config,
        )
        from usethis._integrations.ci.bitbucket.schema import Model, Script
        from usethis._integrations.ci.bitbucket.steps import (
            Step,
            add_bitbucket_step_in_default,
        )
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.file.yaml.io_ import edit_yaml
        from usethis._test import change_cwd

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_bitbucket_pipeline_config()
            add_bitbucket_step_in_default(
                Step(
                    name="Example step",
                    script=Script(
                        [ScriptItemAnchor(name="install-uv"), "echo 'Hello, world!'"]
                    ),
                ),
            )

        # Assert
        with edit_yaml(uv_init_dir / "bitbucket-pipelines.yml") as yaml_document:
            assert Model.model_validate(yaml_document.content)


class TestRemoveBitbucketPipelineConfig:
    def test_blank_slate(self, tmp_path: Path):
        from usethis._integrations.ci.bitbucket.config import (
            remove_bitbucket_pipeline_config,
        )
        from usethis._test import change_cwd

        with change_cwd(tmp_path):
            remove_bitbucket_pipeline_config()

        assert not (tmp_path / "bitbucket-pipelines.yml").exists()

    def test_existing_file(self, tmp_path: Path):
        from usethis._integrations.ci.bitbucket.config import (
            remove_bitbucket_pipeline_config,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").touch()

        with change_cwd(tmp_path):
            remove_bitbucket_pipeline_config()

        assert not (tmp_path / "bitbucket-pipelines.yml").exists()
