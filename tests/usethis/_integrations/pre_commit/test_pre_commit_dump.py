import pytest


class TesttPreCommitFancyDump:
    def test_placeholder(self):
        from usethis._integrations.pre_commit.dump import pre_commit_fancy_dump
        from usethis._integrations.pre_commit.hooks import _get_placeholder_repo_config
        from usethis._integrations.pre_commit.schema import (
            JsonSchemaForPreCommitConfigYaml,
        )

        pre_commit_fancy_dump(
            config=JsonSchemaForPreCommitConfigYaml(
                repos=[
                    _get_placeholder_repo_config(),
                ]
            ),
            reference={},
        )

    def test_invalid(self):
        from usethis._integrations.pre_commit.dump import pre_commit_fancy_dump

        with pytest.raises(TypeError):
            pre_commit_fancy_dump(
                config=2,  # type: ignore for test
                reference={},
            )
