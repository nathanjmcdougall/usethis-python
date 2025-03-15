from pathlib import Path

import pytest

from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.python.version import get_python_version
from usethis._integrations.sonarqube.config import (
    _validate_project_key,
    get_sonar_project_properties,
)
from usethis._integrations.sonarqube.errors import (
    CoverageReportConfigNotFoundError,
    InvalidSonarQubeProjectKeyError,
    MissingProjectKeyError,
)
from usethis._integrations.uv.init import ensure_pyproject_toml
from usethis._integrations.uv.python import python_pin
from usethis._test import change_cwd


class TestGetSonarProjectProperties:
    def test_dump_file(self, tmp_path: Path):
        # If the file already exists, we just return it.

        # Arrange
        path = tmp_path / "sonar-project.properties"
        contents = "foo=bar\n"
        path.write_text(contents)

        # Act
        with change_cwd(tmp_path):
            result = get_sonar_project_properties()

        # Assert
        assert result == contents

    def test_file_not_exists(self, uv_init_dir: Path):
        # If the file does not exist, we should construct based on information in
        # the repo.

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            # Arrange
            PyprojectTOMLManager().set_value(
                keys=["tool", "usethis", "sonarqube", "project-key"], value="foobar"
            )
            PyprojectTOMLManager().set_value(
                keys=["tool", "coverage", "xml", "output"], value="coverage.xml"
            )
            python_pin("3.12")

            # Act
            result = get_sonar_project_properties()

        # Assert
        assert (
            result
            == """\
sonar.projectKey=foobar
sonar.language=py
sonar.python.version=3.12
sonar.sources=./src
sonar.tests=./tests
sonar.python.coverage.reportPaths=coverage.xml
sonar.verbose=false
"""
        )

    def test_different_python_version(self, tmp_path: Path):
        # If the python version is different, it should be updated.

        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Arrange
            assert get_python_version()
            python_pin("3.10")
            ensure_pyproject_toml()
            PyprojectTOMLManager().set_value(
                keys=["tool", "usethis", "sonarqube", "project-key"], value="foobar"
            )
            PyprojectTOMLManager().set_value(
                keys=["tool", "coverage", "xml", "output"], value="coverage.xml"
            )

            # Act
            result = get_sonar_project_properties()

        # Assert
        assert (
            result
            == """\
sonar.projectKey=foobar
sonar.language=py
sonar.python.version=3.10
sonar.sources=./
sonar.tests=./tests
sonar.python.coverage.reportPaths=coverage.xml
sonar.verbose=false
"""
        )

    def test_no_pin_python(self, tmp_path: Path):
        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Arrange
            ensure_pyproject_toml()
            PyprojectTOMLManager().set_value(
                keys=["tool", "usethis", "sonarqube", "project-key"], value="foobar"
            )
            PyprojectTOMLManager().set_value(
                keys=["tool", "coverage", "xml", "output"], value="coverage.xml"
            )

            # Act
            result = get_sonar_project_properties()

        # Assert
        assert (
            result
            == f"""\
sonar.projectKey=foobar
sonar.language=py
sonar.python.version={get_python_version()}
sonar.sources=./
sonar.tests=./tests
sonar.python.coverage.reportPaths=coverage.xml
sonar.verbose=false
"""
        )

    def test_different_project_key(self, tmp_path: Path):
        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Arrange
            python_pin("3.12")
            ensure_pyproject_toml()
            PyprojectTOMLManager().set_value(
                keys=["tool", "usethis", "sonarqube", "project-key"], value="different"
            )
            PyprojectTOMLManager().set_value(
                keys=["tool", "coverage", "xml", "output"], value="coverage.xml"
            )

            # Act
            result = get_sonar_project_properties()

        # Assert
        assert (
            result
            == """\
sonar.projectKey=different
sonar.language=py
sonar.python.version=3.12
sonar.sources=./
sonar.tests=./tests
sonar.python.coverage.reportPaths=coverage.xml
sonar.verbose=false
"""
        )

    def test_set_verbose_true(self, tmp_path: Path):
        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Arrange
            python_pin("3.12")
            ensure_pyproject_toml()
            PyprojectTOMLManager().set_value(
                keys=["tool", "usethis", "sonarqube", "project-key"], value="foobar"
            )
            PyprojectTOMLManager().set_value(
                keys=["tool", "usethis", "sonarqube", "verbose"], value=True
            )
            PyprojectTOMLManager().set_value(
                keys=["tool", "coverage", "xml", "output"], value="coverage.xml"
            )

            # Act
            result = get_sonar_project_properties()

        # Assert
        assert (
            result
            == """\
sonar.projectKey=foobar
sonar.language=py
sonar.python.version=3.12
sonar.sources=./
sonar.tests=./tests
sonar.python.coverage.reportPaths=coverage.xml
sonar.verbose=true
"""
        )

    def test_missing_pyproject_toml_raises(self, tmp_path: Path):
        with (
            change_cwd(tmp_path),
            PyprojectTOMLManager(),
            pytest.raises(MissingProjectKeyError),
        ):
            get_sonar_project_properties()

    def test_missing_project_key_section_raises(self, tmp_path: Path):
        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Arrange
            ensure_pyproject_toml()

            # Act, Assert
            with pytest.raises(MissingProjectKeyError):
                get_sonar_project_properties()

    def test_patch_version_ignored(self, tmp_path: Path):
        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Arrange
            python_pin("3.12.1")
            ensure_pyproject_toml()
            PyprojectTOMLManager().set_value(
                keys=["tool", "usethis", "sonarqube", "project-key"], value="foobar"
            )
            PyprojectTOMLManager().set_value(
                keys=["tool", "coverage", "xml", "output"], value="coverage.xml"
            )

            # Act
            result = get_sonar_project_properties()

        # Assert
        assert (
            result
            == """\
sonar.projectKey=foobar
sonar.language=py
sonar.python.version=3.12
sonar.sources=./
sonar.tests=./tests
sonar.python.coverage.reportPaths=coverage.xml
sonar.verbose=false
"""
        )

    def test_exclusions(self, tmp_path: Path):
        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Arrange
            python_pin("3.12")
            ensure_pyproject_toml()
            PyprojectTOMLManager().set_value(
                keys=["tool", "usethis", "sonarqube", "project-key"], value="foobar"
            )
            PyprojectTOMLManager().set_value(
                keys=["tool", "usethis", "sonarqube", "exclusions"],
                value=[
                    "**/Dockerfile",
                    "src/notebooks/**/*",
                ],
            )
            PyprojectTOMLManager().set_value(
                keys=["tool", "coverage", "xml", "output"], value="coverage.xml"
            )

            # Act
            result = get_sonar_project_properties()

        # Assert
        assert (
            result
            == """\
sonar.projectKey=foobar
sonar.language=py
sonar.python.version=3.12
sonar.sources=./
sonar.tests=./tests
sonar.python.coverage.reportPaths=coverage.xml
sonar.verbose=false
sonar.exclusions=**/Dockerfile, src/notebooks/**/*
"""
        )

    def test_different_coverage_file_location(self, tmp_path: Path):
        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Arrange
            python_pin("3.12")
            ensure_pyproject_toml()
            PyprojectTOMLManager().set_value(
                keys=["tool", "usethis", "sonarqube", "project-key"], value="foobar"
            )
            PyprojectTOMLManager().set_value(
                keys=["tool", "coverage", "xml", "output"],
                value="./test-reports/cov.xml",
            )

            # Act
            result = get_sonar_project_properties()

        # Assert
        assert (
            result
            == """\
sonar.projectKey=foobar
sonar.language=py
sonar.python.version=3.12
sonar.sources=./
sonar.tests=./tests
sonar.python.coverage.reportPaths=./test-reports/cov.xml
sonar.verbose=false
"""
        )

    def test_missing_coverage_file_location_error(self, tmp_path: Path):
        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Arrange
            python_pin("3.12")
            ensure_pyproject_toml()
            PyprojectTOMLManager().set_value(
                keys=["tool", "usethis", "sonarqube", "project-key"], value="foobar"
            )

            # Act, Assert
            with pytest.raises(CoverageReportConfigNotFoundError):
                get_sonar_project_properties()


class TestValidateProjectKey:
    def test_valid(self):
        # Arrange
        project_key = "foo:bar"

        # Act
        result = _validate_project_key(project_key)

        # Assert
        assert result is None

    def test_bad_characters(self):
        # Arrange
        project_key = "foo bar"

        # Act, Assert
        with pytest.raises(InvalidSonarQubeProjectKeyError):
            _validate_project_key(project_key)

    def test_missing_non_digit(self):
        # The key must contain at least one non-digit character.

        # Arrange
        project_key = "123"

        # Act, Assert
        with pytest.raises(InvalidSonarQubeProjectKeyError):
            _validate_project_key(project_key)
