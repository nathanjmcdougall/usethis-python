from pathlib import Path

import pytest


class TestAddCaches:
    def test_in_caches(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._integrations.ci.bitbucket.cache import (
            add_caches,
            get_cache_by_name,
        )
        from usethis._integrations.ci.bitbucket.config import (
            add_bitbucket_pipeline_config,
        )
        from usethis._integrations.ci.bitbucket.schema import Cache, CachePath
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        cache_by_name = {"example": Cache(CachePath("~/.cache/example"))}

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_bitbucket_pipeline_config()
            capfd.readouterr()

            # Act
            add_caches(cache_by_name)

            # Assert
            default_cache_by_name = {"uv": Cache(CachePath("~/.cache/uv"))}
            assert get_cache_by_name() == cache_by_name | default_cache_by_name
            out, err = capfd.readouterr()
            assert not err
            assert out == (
                "✔ Adding cache 'example' definition to 'bitbucket-pipelines.yml'.\n"
            )

    def test_already_exists(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.cache import (
            add_caches,
            get_cache_by_name,
        )
        from usethis._integrations.ci.bitbucket.config import (
            add_bitbucket_pipeline_config,
        )
        from usethis._integrations.ci.bitbucket.schema import Cache, CachePath
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        cache_by_name = {
            "uv": Cache(CachePath("~/.cache/uv"))  # uv cache is in the default config
        }

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_bitbucket_pipeline_config()
            add_caches(cache_by_name)

            # Assert
            assert get_cache_by_name() == cache_by_name

    def test_definitions_order(self, tmp_path: Path):
        """Test that the newly-created definitions section is placed after the image."""
        # Arrange
        from usethis._integrations.ci.bitbucket.cache import add_caches
        from usethis._integrations.ci.bitbucket.schema import Cache, CachePath
        from usethis._test import change_cwd

        cache_by_name = {"example": Cache(CachePath("~/.cache/example"))}

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            script: ["echo 'Hello, world!'"]
"""
        )

        # Act
        with change_cwd(tmp_path):
            add_caches(cache_by_name)

        # Assert
        contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert (
            contents
            == """\
image: atlassian/default-image:3
definitions:
    caches:
        example: ~/.cache/example
pipelines:
    default:
      - step:
            script: ["echo 'Hello, world!'"]
"""
        )


class TestRemoveCache:
    def test_removal_succeeds(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._integrations.ci.bitbucket.cache import remove_cache
        from usethis._test import change_cwd

        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
definitions:
    caches:
        uv: ~/.cache/uv
pipelines:
    default:
      - step:
            caches: [uv]
            script: ["echo 'Hello, world!'"]
"""
        )

        # Act
        with change_cwd(tmp_path):
            remove_cache("uv")

        # Assert
        (tmp_path / "bitbucket-pipelines.yml").write_text(
            """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            caches: [uv]
            script: ["echo 'Hello, world!'"]
"""
        )
        out, err = capfd.readouterr()
        assert not err
        assert (
            out == "✔ Removing cache 'uv' definition from 'bitbucket-pipelines.yml'.\n"
        )

    def test_roundtrip(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.cache import (
            add_caches,
            get_cache_by_name,
            remove_cache,
        )
        from usethis._integrations.ci.bitbucket.config import (
            add_bitbucket_pipeline_config,
        )
        from usethis._integrations.ci.bitbucket.schema import Cache, CachePath
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_bitbucket_pipeline_config()
            add_caches({"mycache": Cache(CachePath("~/.cache/mytool"))})

            # Act
            remove_cache("mycache")

            # Assert
            assert "mycache" not in get_cache_by_name()

    def test_empty_section_not_removed_unnecessarily(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.cache import remove_cache
        from usethis._test import change_cwd

        original = """\
image: atlassian/default-image:3
definitions:
    caches: {}
pipelines:
    default:
      - step:
            script: ["echo 'Hello, world!'"]
"""
        (tmp_path / "bitbucket-pipelines.yml").write_text(original)

        # Act
        with change_cwd(tmp_path):
            remove_cache("whatever")

        # Assert
        contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert contents == original

    def test_no_definitions_section(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.cache import remove_cache
        from usethis._test import change_cwd

        original = """\
image: atlassian/default-image:3
pipelines:
    default:
      - step:
            script: ["echo 'Hello, world!'"]
"""
        (tmp_path / "bitbucket-pipelines.yml").write_text(original)

        # Act
        with change_cwd(tmp_path):
            remove_cache("whatever")

        # Assert
        contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert contents == original

    def test_no_cache_definitions_section(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.ci.bitbucket.cache import remove_cache
        from usethis._test import change_cwd

        original = """\
image: atlassian/default-image:3
definitions:
    something_else: {}
pipelines:
    default:
      - step:
            script: ["echo 'Hello, world!'"]
"""
        (tmp_path / "bitbucket-pipelines.yml").write_text(original)

        # Act
        with change_cwd(tmp_path):
            remove_cache("whatever")

        # Assert
        contents = (tmp_path / "bitbucket-pipelines.yml").read_text()
        assert contents == original
