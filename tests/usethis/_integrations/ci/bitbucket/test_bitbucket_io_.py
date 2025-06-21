from pathlib import Path

import pytest


class TestEditBitbucketPipelinesYAML:
    def test_does_not_exist(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._integrations.ci.bitbucket.io_ import edit_bitbucket_pipelines_yaml
        from usethis._test import change_cwd

        # Act
        with change_cwd(tmp_path), edit_bitbucket_pipelines_yaml() as _:
            pass

        # Assert
        assert (tmp_path / "bitbucket-pipelines.yml").is_file()
        assert (
            (tmp_path / "bitbucket-pipelines.yml").read_text()
            == """\
image: atlassian/default-image:3
"""
        )
        out, err = capfd.readouterr()
        assert not err
        assert out == ("✔ Writing 'bitbucket-pipelines.yml'.\n")

    def test_do_nothing(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.io_ import edit_bitbucket_pipelines_yaml
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
"""
        )

        # Act
        with change_cwd(tmp_path), edit_bitbucket_pipelines_yaml() as _:
            pass

        # Assert
        contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert (
            contents
            == """\
image: atlassian/default-image:3
"""
        )

    def test_change_image(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.io_ import edit_bitbucket_pipelines_yaml
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
"""
        )

        # Act
        with change_cwd(tmp_path), edit_bitbucket_pipelines_yaml() as doc:
            assert isinstance(doc.content, dict)  # Help pyright
            doc.content["image"] = "atlassian/default-image:2"

        # Assert
        contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert (
            contents
            == """\
image: atlassian/default-image:2
"""
        )

    def test_change_default(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.io_ import edit_bitbucket_pipelines_yaml
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
pipelines:
    default:
      - step:
            script:
              - echo 'Hello, world!'
"""
        )

        # Act
        with change_cwd(tmp_path), edit_bitbucket_pipelines_yaml() as doc:
            # Help pyright with assertions
            assert isinstance(doc.content, dict)
            assert isinstance(doc.content["pipelines"], dict)
            assert isinstance(doc.content["pipelines"]["default"], list)
            assert isinstance(doc.content["pipelines"]["default"][0], dict)
            assert isinstance(doc.content["pipelines"]["default"][0]["step"], dict)
            doc.content["pipelines"]["default"][0]["step"]["script"] = ["echo 'Bye!'"]

        # Assert
        contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert (
            contents
            == """\
pipelines:
    default:
      - step:
            script:
              - echo 'Bye!'
"""
        )

    def test_roundtrip_indentation(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.io_ import edit_bitbucket_pipelines_yaml
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
pipelines:
      default:
          - step:
                  script:
                      - echo 'Hello, world!'
"""
        )

        # Act
        with change_cwd(tmp_path), edit_bitbucket_pipelines_yaml() as _:
            pass

        # Assert
        contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert (
            contents
            == """\
pipelines:
      default:
          - step:
                  script:
                      - echo 'Hello, world!'
"""
        )

    def test_invalid_contents(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.io_ import (
            BitbucketPipelinesYAMLConfigError,
            edit_bitbucket_pipelines_yaml,
        )
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text("""\
awfpah28yqh2an ran  2rqa0-2 }[
""")

        # Act, Assert
        with (
            change_cwd(tmp_path),
            pytest.raises(BitbucketPipelinesYAMLConfigError),
            edit_bitbucket_pipelines_yaml() as _,
        ):
            pass
