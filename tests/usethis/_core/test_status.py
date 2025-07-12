from pathlib import Path

import pytest

from usethis._core.status import use_development_status
from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._test import change_cwd
from usethis._types.status import DevelopmentStatusEnum


class TestUseDevelopmentStatus:
    def test_planning(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        status = DevelopmentStatusEnum.planning

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            use_development_status(status)

        # Assert
        assert (
            "Development Status :: 1 - Planning"
            in uv_init_dir.joinpath("pyproject.toml").read_text()
        )
        with PyprojectTOMLManager() as mgr:
            assert (
                "Development Status :: 1 - Planning" in mgr[["project", "classifiers"]]
            )
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Setting the development status to '1 - Planning'.\n"

    def test_planning_code(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        status = DevelopmentStatusEnum.planning_code

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            use_development_status(status)

        # Assert
        assert (
            "Development Status :: 1 - Planning"
            in uv_init_dir.joinpath("pyproject.toml").read_text()
        )
        with PyprojectTOMLManager() as mgr:
            assert (
                "Development Status :: 1 - Planning" in mgr[["project", "classifiers"]]
            )
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Setting the development status to '1 - Planning'.\n"

    def test_prealpha(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        status = DevelopmentStatusEnum.prealpha

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            use_development_status(status)

        # Assert
        assert (
            "Development Status :: 2 - Pre-Alpha"
            in uv_init_dir.joinpath("pyproject.toml").read_text()
        )
        with PyprojectTOMLManager() as mgr:
            assert (
                "Development Status :: 2 - Pre-Alpha" in mgr[["project", "classifiers"]]
            )
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Setting the development status to '2 - Pre-Alpha'.\n"

    def test_alpha(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        status = DevelopmentStatusEnum.alpha

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            use_development_status(status)

        # Assert
        assert (
            "Development Status :: 3 - Alpha"
            in uv_init_dir.joinpath("pyproject.toml").read_text()
        )
        with PyprojectTOMLManager() as mgr:
            assert "Development Status :: 3 - Alpha" in mgr[["project", "classifiers"]]
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Setting the development status to '3 - Alpha'.\n"

    def test_beta(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        status = DevelopmentStatusEnum.beta

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            use_development_status(status)

        # Assert
        assert (
            "Development Status :: 4 - Beta"
            in uv_init_dir.joinpath("pyproject.toml").read_text()
        )
        with PyprojectTOMLManager() as mgr:
            assert "Development Status :: 4 - Beta" in mgr[["project", "classifiers"]]
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Setting the development status to '4 - Beta'.\n"

    def test_production(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        status = DevelopmentStatusEnum.production

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            use_development_status(status)

        # Assert
        assert (
            "Development Status :: 5 - Production/Stable"
            in uv_init_dir.joinpath("pyproject.toml").read_text()
        )
        with PyprojectTOMLManager() as mgr:
            assert (
                "Development Status :: 5 - Production/Stable"
                in mgr[["project", "classifiers"]]
            )
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Setting the development status to '5 - Production/Stable'.\n"

    def test_mature(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        status = DevelopmentStatusEnum.mature

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            use_development_status(status)

        # Assert
        assert (
            "Development Status :: 6 - Mature"
            in uv_init_dir.joinpath("pyproject.toml").read_text()
        )
        with PyprojectTOMLManager() as mgr:
            assert "Development Status :: 6 - Mature" in mgr[["project", "classifiers"]]
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Setting the development status to '6 - Mature'.\n"

    def test_inactive(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        status = DevelopmentStatusEnum.inactive

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            use_development_status(status)

        # Assert
        assert (
            "Development Status :: 7 - Inactive"
            in uv_init_dir.joinpath("pyproject.toml").read_text()
        )
        with PyprojectTOMLManager() as mgr:
            assert (
                "Development Status :: 7 - Inactive" in mgr[["project", "classifiers"]]
            )
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Setting the development status to '7 - Inactive'.\n"

    def test_no_pyproject_toml(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        status = DevelopmentStatusEnum.planning

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            use_development_status(status)

        # Assert
        out, err = capfd.readouterr()
        assert not err
        assert out == (
            "✔ Writing 'pyproject.toml'.\n"
            "✔ Setting the development status to '1 - Planning'.\n"
        )

    def test_replace_existing_classifier(
        self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
    ):
        # Arrange
        status = DevelopmentStatusEnum.beta

        # Create an existing classifier
        (uv_init_dir / "pyproject.toml").write_text(
            """\
[project]
classifiers = [
    "Development Status :: 3 - Alpha",
]
"""
        )

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            use_development_status(status)

        # Assert
        assert (
            "Development Status :: 4 - Beta"
            in uv_init_dir.joinpath("pyproject.toml").read_text()
        )
        with PyprojectTOMLManager() as mgr:
            assert mgr[["project", "classifiers"]] == ["Development Status :: 4 - Beta"]
            assert (
                "Development Status :: 3 - Alpha" not in mgr[["project", "classifiers"]]
            )
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Setting the development status to '4 - Beta'.\n"

    def test_replace_multiple_existing_classifiers(
        self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
    ):
        # Arrange
        status = DevelopmentStatusEnum.production

        # Create existing classifiers
        (uv_init_dir / "pyproject.toml").write_text(
            """\
[project]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Development Status :: 4 - Beta",
]
"""
        )

        # Act
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            use_development_status(status)

        # Assert
        assert (
            "Development Status :: 5 - Production/Stable"
            in uv_init_dir.joinpath("pyproject.toml").read_text()
        )
        with PyprojectTOMLManager() as mgr:
            assert mgr[["project", "classifiers"]] == [
                "Development Status :: 5 - Production/Stable"
            ]
            assert (
                "Development Status :: 3 - Alpha" not in mgr[["project", "classifiers"]]
            )
            assert (
                "Development Status :: 4 - Beta" not in mgr[["project", "classifiers"]]
            )
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Setting the development status to '5 - Production/Stable'.\n"
