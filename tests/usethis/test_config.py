from pathlib import Path

import pytest


class TestUsethisConfig:
    class TestCPD:
        def test_matches_path_cwd(self, tmp_path: Path):
            # Arrange
            from usethis._config import UsethisConfig
            from usethis._test import change_cwd

            config = UsethisConfig()

            # Act
            with change_cwd(tmp_path):
                cwd = config.cpd()

            # Assert
            assert cwd == tmp_path

        def test_set_overrides_cwd(self, tmp_path: Path):
            # Arrange
            from usethis._config import UsethisConfig
            from usethis._test import change_cwd

            config = UsethisConfig()

            # Act
            with (
                change_cwd(tmp_path),
                config.set(project_dir=Path("42 Wallaby Way, Sydney")),
            ):
                project_dir = config.cpd()

            # Assert
            assert project_dir == Path("42 Wallaby Way, Sydney")

    class TestDisableUVSubprocess:
        def test_raises_error_when_disabled(self):
            # Arrange
            from usethis._config import usethis_config
            from usethis._integrations.uv.call import call_uv_subprocess
            from usethis._integrations.uv.errors import UVSubprocessFailedError
            from usethis._test import change_cwd

            # Act & Assert
            with (
                change_cwd(Path.cwd()),
                usethis_config.set(disable_uv_subprocess=True),
                pytest.raises(UVSubprocessFailedError),
            ):
                call_uv_subprocess(["python", "list"], change_toml=False)

        def test_does_not_raise_error_when_enabled(self):
            # Arrange
            from usethis._config import usethis_config
            from usethis._integrations.uv.call import call_uv_subprocess
            from usethis._test import change_cwd

            # Act & Assert
            with (
                change_cwd(Path.cwd()),
                usethis_config.set(disable_uv_subprocess=False),
            ):
                output = call_uv_subprocess(["python", "list"], change_toml=False)

            assert output is not None
