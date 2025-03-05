from pathlib import Path
from typing import Any

import pytest

import usethis._integrations.uv.call
from usethis._integrations.pyproject_toml.core import do_pyproject_id_keys_exist
from usethis._integrations.pyproject_toml.errors import PyprojectTOMLInitError
from usethis._integrations.pyproject_toml.io_ import PyprojectTOMLManager
from usethis._integrations.uv.errors import UVSubprocessFailedError
from usethis._integrations.uv.init import ensure_pyproject_toml
from usethis._test import change_cwd


class TestEnsurePyprojectTOML:
    def test_created(self, tmp_path: Path, capfd: pytest.CaptureFixture[str]):
        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            ensure_pyproject_toml()

        # Assert
        assert (tmp_path / "pyproject.toml").exists()
        out, err = capfd.readouterr()
        assert not err
        assert out == "✔ Writing 'pyproject.toml'.\n"

    def test_already_exists_unchanged(
        self, tmp_path: Path, capfd: pytest.CaptureFixture[str]
    ):
        # Arrange
        (tmp_path / "pyproject.toml").write_text("test")

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            ensure_pyproject_toml()

        # Assert
        assert (tmp_path / "pyproject.toml").read_text() == "test"
        out, err = capfd.readouterr()
        assert not err
        assert not out

    def test_hello_py_respected(self, tmp_path: Path):
        # Arrange
        (tmp_path / "hello.py").write_text("test")

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            ensure_pyproject_toml()

        # Assert
        assert (tmp_path / "hello.py").exists()
        assert (tmp_path / "hello.py").read_text() == "test"

    def test_main_py_respected(self, tmp_path: Path):
        # Arrange
        (tmp_path / "main.py").write_text("test")

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            ensure_pyproject_toml()

        # Assert
        assert (tmp_path / "main.py").exists()
        assert (tmp_path / "main.py").read_text() == "test"

    def test_no_hello_py_created(self, tmp_path: Path):
        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            ensure_pyproject_toml()

        # Assert
        assert not (tmp_path / "hello.py").exists()

    def test_no_main_py_created(self, tmp_path: Path):
        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            ensure_pyproject_toml()

        # Assert
        assert not (tmp_path / "main.py").exists()

    def test_no_readme(self, tmp_path: Path):
        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            ensure_pyproject_toml()

        # Assert
        assert not (tmp_path / "README.md").exists()

    def test_no_pin_python(self, tmp_path: Path):
        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            ensure_pyproject_toml()

        # Assert
        assert not (tmp_path / ".python-version").exists()

    def test_no_vcs(self, tmp_path: Path):
        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            ensure_pyproject_toml()

        # Assert
        assert not (tmp_path / ".git").exists()

    def test_subprocess_failed(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Arrange
        def mock_call_uv_subprocess(*args: Any, **kwargs: Any) -> None:
            raise UVSubprocessFailedError

        monkeypatch.setattr(
            usethis._integrations.uv.call,
            "call_uv_subprocess",
            mock_call_uv_subprocess,
        )

        # Act
        with (
            change_cwd(tmp_path),
            PyprojectTOMLManager(),
            pytest.raises(PyprojectTOMLInitError),
        ):
            ensure_pyproject_toml()

    def test_build_backend(self, tmp_path: Path):
        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Act
            ensure_pyproject_toml()

            # Assert
            assert do_pyproject_id_keys_exist(id_keys=["build-system"])
