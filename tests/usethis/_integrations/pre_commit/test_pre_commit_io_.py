from pathlib import Path

import pytest


class TestEditPreCommitConfigYAML:
    def test_does_not_exist(self, tmp_path: Path):
        from usethis._integrations.pre_commit.io_ import edit_pre_commit_config_yaml
        from usethis._test import change_cwd

        with change_cwd(tmp_path), edit_pre_commit_config_yaml():
            pass

        assert (tmp_path / ".pre-commit-config.yaml").exists()

    def test_unchanged(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.pre_commit.io_ import edit_pre_commit_config_yaml
        from usethis._test import change_cwd

        content_str = """\
repos:
  - repo: https://github.com/abravalheri/validate-pyproject
    rev: v0.23
    hooks:
      - id: validate-pyproject
        additional_dependencies: ['validate-pyproject-schema-store[all]']
"""
        (tmp_path / ".pre-commit-config.yaml").write_text(content_str)

        # Act
        with change_cwd(tmp_path), edit_pre_commit_config_yaml() as _:
            pass

        # Assert
        assert (tmp_path / ".pre-commit-config.yaml").read_text() == content_str

    def test_empty_is_invalid(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.pre_commit.io_ import (
            PreCommitConfigYAMLConfigError,
            edit_pre_commit_config_yaml,
        )
        from usethis._test import change_cwd

        (tmp_path / ".pre-commit-config.yaml").write_text("")

        # Act, Assert
        with (
            change_cwd(tmp_path),
            pytest.raises(PreCommitConfigYAMLConfigError),
            edit_pre_commit_config_yaml(),
        ):
            pass
