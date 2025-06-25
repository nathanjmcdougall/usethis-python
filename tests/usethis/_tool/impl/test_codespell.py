import os
from pathlib import Path

import pytest

from usethis._config_file import files_manager
from usethis._core.tool import use_codespell
from usethis._integrations.ci.github.errors import GitHubTagError
from usethis._integrations.ci.github.tags import get_github_latest_tag
from usethis._integrations.pre_commit.schema import UriRepo
from usethis._test import change_cwd
from usethis._tool.impl.codespell import CodespellTool


class TestCodespellTool:
    class TestPrintHowToUse:
        def test_pre_commit_used_but_not_configured(
            self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
        ):
            # https://github.com/usethis-python/usethis-python/issues/802

            # Arrange
            with change_cwd(uv_init_dir), files_manager():
                use_codespell()
            capfd.readouterr()

            (uv_init_dir / ".pre-commit-config.yaml").touch()

            # Act
            with change_cwd(uv_init_dir), files_manager():
                CodespellTool().print_how_to_use()

            # Assert
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Run 'uv run codespell' to run the Codespell spellchecker.\n"
            )

    def test_latest_version(self):
        (config,) = CodespellTool().get_pre_commit_config().repo_configs
        repo = config.repo
        assert isinstance(repo, UriRepo)
        try:
            assert repo.rev == get_github_latest_tag(
                owner="codespell-project", repo="codespell"
            )
        except GitHubTagError as err:
            if os.getenv("CI"):
                pytest.skip(
                    "Failed to fetch GitHub tags (connection issues); skipping test"
                )
            raise err
