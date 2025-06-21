from pathlib import Path

import pytest


class TestGetDepGroups:
    def test_no_dev_section(self, tmp_path: Path):
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import get_dep_groups
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").touch()

        with change_cwd(tmp_path), PyprojectTOMLManager():
            assert get_dep_groups() == {}

    def test_empty_section(self, tmp_path: Path):
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import get_dep_groups
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("""\
[dependency-groups]
""")

        with change_cwd(tmp_path), PyprojectTOMLManager():
            assert get_dep_groups() == {}

    def test_empty_group(self, tmp_path: Path):
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import get_dep_groups
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("""\
[dependency-groups]
test=[]
""")

        with change_cwd(tmp_path), PyprojectTOMLManager():
            assert get_dep_groups() == {"test": []}

    def test_single_dev_dep(self, tmp_path: Path):
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import Dependency, get_dep_groups
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("""\
[dependency-groups]
test=['pytest']
""")

        with change_cwd(tmp_path), PyprojectTOMLManager():
            assert get_dep_groups() == {"test": [Dependency(name="pytest")]}

    def test_multiple_dev_deps(self, tmp_path: Path):
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import Dependency, get_dep_groups
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("""\
[dependency-groups]
qa=["flake8", "black", "isort"]
""")

        with change_cwd(tmp_path), PyprojectTOMLManager():
            assert get_dep_groups() == {
                "qa": [
                    Dependency(name="flake8"),
                    Dependency(name="black"),
                    Dependency(name="isort"),
                ]
            }

    def test_multiple_groups(self, tmp_path: Path):
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import Dependency, get_dep_groups
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text(
            """\
[dependency-groups]
qa=["flake8", "black", "isort"]
test=['pytest']
"""
        )

        with change_cwd(tmp_path), PyprojectTOMLManager():
            assert get_dep_groups() == {
                "qa": [
                    Dependency(name="flake8"),
                    Dependency(name="black"),
                    Dependency(name="isort"),
                ],
                "test": [
                    Dependency(name="pytest"),
                ],
            }

    def test_no_pyproject(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import get_dep_groups
        from usethis._test import change_cwd

        # Act
        with change_cwd(tmp_path), PyprojectTOMLManager():
            result = get_dep_groups()

        # Assert
        assert result == {}


class TestAddDepsToGroup:
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_pyproject_changed(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            Dependency,
            add_deps_to_group,
            get_deps_from_group,
            is_dep_satisfied_in,
        )
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            # Act
            add_deps_to_group([Dependency(name="pytest")], "test")

            # Assert
            assert is_dep_satisfied_in(
                Dependency(name="pytest"), in_=get_deps_from_group("test")
            )

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_single_dep(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            Dependency,
            add_deps_to_group,
            get_deps_from_group,
        )
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            # Act
            add_deps_to_group([Dependency(name="pytest")], "test")

            # Assert
            assert get_deps_from_group("test") == [Dependency(name="pytest")]
            out, err = capfd.readouterr()
            assert not err
            assert (
                out
                == "✔ Adding dependency 'pytest' to the 'test' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'pytest'.\n"
            )

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_multiple_deps(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            Dependency,
            add_deps_to_group,
            get_deps_from_group,
        )
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            # Act
            add_deps_to_group(
                [Dependency(name="flake8"), Dependency(name="black")], "qa"
            )

            # Assert
            assert set(get_deps_from_group("qa")) == {
                Dependency(name="flake8"),
                Dependency(name="black"),
            }
            out, err = capfd.readouterr()
            assert not err
            assert (
                out
                == "✔ Adding dependencies 'flake8', 'black' to the 'qa' group in 'pyproject.toml'.\n"
                "☐ Install the dependencies 'flake8', 'black'.\n"
            )

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_multi_but_one_already_exists(
        self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
    ):
        # Arrange
        from usethis._config import usethis_config
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            Dependency,
            add_deps_to_group,
            get_deps_from_group,
        )
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            with usethis_config.set(quiet=True):
                add_deps_to_group([Dependency(name="pytest")], "test")

            # Act
            add_deps_to_group(
                [Dependency(name="pytest"), Dependency(name="black")], "test"
            )

            # Assert
            assert set(get_deps_from_group("test")) == {
                Dependency(name="pytest"),
                Dependency(name="black"),
            }
            out, err = capfd.readouterr()
            assert not err
            assert (
                out
                == "✔ Adding dependency 'black' to the 'test' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'black'.\n"
            )

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_extras(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            Dependency,
            add_deps_to_group,
            get_deps_from_group,
            is_dep_satisfied_in,
        )
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            # Act
            add_deps_to_group(
                [Dependency(name="pytest", extras=frozenset({"extra"}))], "test"
            )

            # Assert
            assert is_dep_satisfied_in(
                Dependency(name="pytest", extras=frozenset({"extra"})),
                in_=get_deps_from_group("test"),
            )
            content = (uv_init_dir / "pyproject.toml").read_text()
            assert "pytest[extra]" in content
            out, err = capfd.readouterr()
            assert not err
            assert (
                out
                == "✔ Adding dependency 'pytest' to the 'test' group in 'pyproject.toml'.\n"
                "☐ Install the dependency 'pytest'.\n"
            )

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_empty_deps(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            add_deps_to_group,
            get_deps_from_group,
        )
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            # Act
            add_deps_to_group([], "test")

            # Assert
            assert not get_deps_from_group("test")
            out, err = capfd.readouterr()
            assert not err
            assert not out

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_extra_when_nonextra_already_present(self, uv_init_dir: Path):
        # https://github.com/usethis-python/usethis-python/issues/227
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import Dependency, add_deps_to_group
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_deps_to_group([Dependency(name="coverage")], "test")

            # Act
            add_deps_to_group(
                [Dependency(name="coverage", extras=frozenset({"toml"}))], "test"
            )

            # Assert
            content = (uv_init_dir / "pyproject.toml").read_text()
            assert "coverage[toml]" in content

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_extras_combining_together(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import Dependency, add_deps_to_group
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_deps_to_group(
                [Dependency(name="coverage", extras=frozenset({"toml"}))], "test"
            )

            # Act
            add_deps_to_group(
                [Dependency(name="coverage", extras=frozenset({"extra"}))], "test"
            )

            # Assert
            content = (uv_init_dir / "pyproject.toml").read_text()
            assert "coverage[extra,toml]" in content

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_combine_extras_alphabetical(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import Dependency, add_deps_to_group
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_deps_to_group(
                [Dependency(name="coverage", extras=frozenset({"extra"}))], "test"
            )

            # Act
            add_deps_to_group(
                [Dependency(name="coverage", extras=frozenset({"toml"}))], "test"
            )

            # Assert
            content = (uv_init_dir / "pyproject.toml").read_text()
            assert "coverage[extra,toml]" in content

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_registers_default_group(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import Dependency, add_deps_to_group
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            # Act
            add_deps_to_group([Dependency(name="pytest")], "test")

            # Assert
            default_groups = PyprojectTOMLManager()[["tool", "uv", "default-groups"]]
            assert "test" in default_groups

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_dev_group_not_registered(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import Dependency, add_deps_to_group
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            # Act
            add_deps_to_group([Dependency(name="black")], "dev")

            # Assert
            assert ["tool", "uv", "default-groups"] not in PyprojectTOMLManager()

    def test_uv_subprocess_error(
        self, uv_init_dir: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange
        import usethis._integrations
        import usethis._integrations.uv
        import usethis._integrations.uv.deps
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            Dependency,
            add_deps_to_group,
            get_default_groups,
        )
        from usethis._integrations.uv.errors import (
            UVDepGroupError,
            UVSubprocessFailedError,
        )
        from usethis._test import change_cwd

        def mock_call_uv_subprocess(*_, **__):
            raise UVSubprocessFailedError

        monkeypatch.setattr(
            usethis._integrations.uv.deps, "call_uv_subprocess", mock_call_uv_subprocess
        )

        # Act, Assert
        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            with pytest.raises(
                UVDepGroupError,
                match="Failed to add 'pytest' to the 'test' dependency group",
            ):
                add_deps_to_group([Dependency(name="pytest")], "test")

            # Assert contd
            # We want to check that registration hasn't taken place
            default_groups = get_default_groups()
            assert "test" not in default_groups


class TestRemoveDepsFromGroup:
    @pytest.mark.usefixtures("_vary_network_conn")
    def test_pyproject_changed(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            Dependency,
            add_deps_to_group,
            get_deps_from_group,
            remove_deps_from_group,
        )
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_deps_to_group([Dependency(name="pytest")], "test")

            # Act
            remove_deps_from_group([Dependency(name="pytest")], "test")

            # Assert
            assert "pytest" not in get_deps_from_group("test")

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_single_dep(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._config import usethis_config
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            Dependency,
            add_deps_to_group,
            get_deps_from_group,
            remove_deps_from_group,
        )
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            with usethis_config.set(quiet=True):
                add_deps_to_group([Dependency(name="pytest")], "test")

            # Act
            remove_deps_from_group([Dependency(name="pytest")], "test")

            # Assert
            assert not get_deps_from_group("test")
            out, err = capfd.readouterr()
            assert not err
            assert (
                out
                == "✔ Removing dependency 'pytest' from the 'test' group in 'pyproject.toml'.\n"
            )

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_multiple_deps(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._config import usethis_config
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            Dependency,
            add_deps_to_group,
            get_deps_from_group,
            remove_deps_from_group,
        )
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            with usethis_config.set(quiet=True):
                add_deps_to_group(
                    [Dependency(name="flake8"), Dependency(name="black")], "qa"
                )

            # Act
            remove_deps_from_group(
                [Dependency(name="flake8"), Dependency(name="black")], "qa"
            )

            # Assert
            assert not get_deps_from_group("qa")
            out, err = capfd.readouterr()
            assert not err
            assert (
                out
                == "✔ Removing dependencies 'flake8', 'black' from the 'qa' group in \n'pyproject.toml'.\n"
            )

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_multi_but_only_not_exists(
        self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
    ):
        # Arrange
        from usethis._config import usethis_config
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            Dependency,
            add_deps_to_group,
            get_deps_from_group,
            remove_deps_from_group,
        )
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            with usethis_config.set(quiet=True):
                add_deps_to_group([Dependency(name="pytest")], "test")

            # Act
            remove_deps_from_group(
                [Dependency(name="pytest"), Dependency(name="black")], "test"
            )

            # Assert
            assert not get_deps_from_group("test")
            out, err = capfd.readouterr()
            assert not err
            assert (
                out
                == "✔ Removing dependency 'pytest' from the 'test' group in 'pyproject.toml'.\n"
            )

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_extras(self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]):
        # Arrange
        from usethis._config import usethis_config
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            Dependency,
            add_deps_to_group,
            get_deps_from_group,
            remove_deps_from_group,
        )
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            with usethis_config.set(quiet=True):
                add_deps_to_group(
                    [Dependency(name="pytest", extras=frozenset({"extra"}))], "test"
                )

            # Act
            remove_deps_from_group(
                [Dependency(name="pytest", extras=frozenset({"extra"}))], "test"
            )

            # Assert
            assert not get_deps_from_group("test")
            out, err = capfd.readouterr()
            assert not err
            assert (
                out
                == "✔ Removing dependency 'pytest' from the 'test' group in 'pyproject.toml'.\n"
            )

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_group_not_in_dependency_groups(
        self, uv_init_dir: Path, capfd: pytest.CaptureFixture[str]
    ):
        # Arrange
        from usethis._config import usethis_config
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            Dependency,
            add_deps_to_group,
            get_deps_from_group,
            remove_deps_from_group,
        )
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            with usethis_config.set(quiet=True):
                add_deps_to_group([Dependency(name="pytest")], "test")

            # Remove the group from dependency-groups but keep it in default-groups
            del PyprojectTOMLManager()[["dependency-groups", "test"]]

            # Act
            remove_deps_from_group([Dependency(name="pytest")], "test")

            # Assert
            assert not get_deps_from_group("test")
            out, err = capfd.readouterr()
            assert not err
            assert not out

    def test_uv_subprocess_error(
        self, uv_init_dir: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange
        import usethis._integrations
        import usethis._integrations.uv
        import usethis._integrations.uv.deps
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            Dependency,
            add_deps_to_group,
            remove_deps_from_group,
        )
        from usethis._integrations.uv.errors import (
            UVDepGroupError,
            UVSubprocessFailedError,
        )
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_deps_to_group([Dependency(name="pytest")], "test")

            def mock_call_uv_subprocess(*_, **__):
                raise UVSubprocessFailedError

            monkeypatch.setattr(
                usethis._integrations.uv.deps,
                "call_uv_subprocess",
                mock_call_uv_subprocess,
            )

            # Act
            with pytest.raises(
                UVDepGroupError,
                match="Failed to remove 'pytest' from the 'test' dependency group",
            ):
                remove_deps_from_group([Dependency(name="pytest")], "test")


class TestIsDepInAnyGroup:
    def test_no_group(self, uv_init_dir: Path):
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import Dependency, is_dep_in_any_group
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            assert not is_dep_in_any_group(Dependency(name="pytest"))

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_in_group(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            Dependency,
            add_deps_to_group,
            is_dep_in_any_group,
        )
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_deps_to_group([Dependency(name="pytest")], "test")

            # Act
            result = is_dep_in_any_group(Dependency(name="pytest"))

        # Assert
        assert result

    @pytest.mark.usefixtures("_vary_network_conn")
    def test_not_in_group(self, uv_init_dir: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import (
            Dependency,
            add_deps_to_group,
            is_dep_in_any_group,
        )
        from usethis._test import change_cwd

        with change_cwd(uv_init_dir), PyprojectTOMLManager():
            add_deps_to_group([Dependency(name="pytest")], "test")

            # Act
            result = is_dep_in_any_group(Dependency(name="black"))

        # Assert
        assert not result


class TestIsDepSatisfiedIn:
    def test_empty(self):
        # Arrange
        from usethis._integrations.uv.deps import Dependency, is_dep_satisfied_in

        dep = Dependency(name="pytest")
        in_ = []

        # Act
        result = is_dep_satisfied_in(dep, in_=in_)

        # Assert
        assert not result

    def test_same(self):
        # Arrange
        from usethis._integrations.uv.deps import Dependency, is_dep_satisfied_in

        dep = Dependency(name="pytest")
        in_ = [Dependency(name="pytest")]

        # Act
        result = is_dep_satisfied_in(dep, in_=in_)

        # Assert
        assert result

    def test_same_name_superset_extra(self):
        # Arrange
        from usethis._integrations.uv.deps import Dependency, is_dep_satisfied_in

        dep = Dependency(name="pytest", extras=frozenset({"extra"}))
        in_ = [Dependency(name="pytest")]

        # Act
        result = is_dep_satisfied_in(dep, in_=in_)

        # Assert
        assert not result

    def test_same_name_subset_extra(self):
        # Arrange
        from usethis._integrations.uv.deps import Dependency, is_dep_satisfied_in

        dep = Dependency(name="pytest")
        in_ = [Dependency(name="pytest", extras=frozenset({"extra"}))]

        # Act
        result = is_dep_satisfied_in(dep, in_=in_)

        # Assert
        assert result

    def test_multiple(self):
        # Arrange
        from usethis._integrations.uv.deps import Dependency, is_dep_satisfied_in

        dep = Dependency(name="pytest")
        in_ = [Dependency(name="flake8"), Dependency(name="pytest")]

        # Act
        result = is_dep_satisfied_in(dep, in_=in_)

        # Assert
        assert result


class TestRegisterDefaultGroup:
    def test_section_not_exists_adds_dev(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import register_default_group
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("")

        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Act
            register_default_group("test")

            # Assert
            default_groups = PyprojectTOMLManager()[["tool", "uv", "default-groups"]]
            assert set(default_groups) == {"test", "dev"}

    def test_empty_section_adds_dev(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import register_default_group
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("""\
[tool.uv]
""")

        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Act
            register_default_group("test")

            # Assert
            default_groups = PyprojectTOMLManager()[["tool", "uv", "default-groups"]]
            assert set(default_groups) == {"test", "dev"}

    def test_empty_default_groups_adds_dev(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import register_default_group
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("""\
[tool.uv]
default-groups = []
""")

        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Act
            register_default_group("test")

            # Assert
            default_groups = PyprojectTOMLManager()[["tool", "uv", "default-groups"]]
            assert set(default_groups) == {"test", "dev"}

    def test_existing_section_no_dev_added_if_no_other_groups(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import register_default_group
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("""\
[tool.uv]
default-groups = ["test"]
""")

        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Act
            register_default_group("test")

            # Assert
            default_groups = PyprojectTOMLManager()[["tool", "uv", "default-groups"]]
            assert set(default_groups) == {"test"}

    def test_existing_section_no_dev_added_if_dev_exists(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import register_default_group
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("""\
[tool.uv]
default-groups = ["test", "dev"]
""")

        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Act
            register_default_group("docs")

            # Assert
            default_groups = PyprojectTOMLManager()[["tool", "uv", "default-groups"]]
            assert set(default_groups) == {"test", "dev", "docs"}

    def test_existing_section_adds_dev_with_new_group(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import register_default_group
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("""\
[tool.uv]
default-groups = ["test"]
""")

        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Act
            register_default_group("docs")

            # Assert
            default_groups = PyprojectTOMLManager()[["tool", "uv", "default-groups"]]
            assert set(default_groups) == {"test", "docs", "dev"}

    def test_dev_not_added_if_missing(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import register_default_group
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("""\
[tool.uv]
default-groups = ["test"]
""")

        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Act
            register_default_group("test")

            # Assert
            default_groups = PyprojectTOMLManager()[["tool", "uv", "default-groups"]]
            assert set(default_groups) == {"test"}


class TestAddDefaultGroups:
    def test_uv_toml(self, tmp_path: Path):
        # Arrange
        from usethis._config_file import files_manager
        from usethis._integrations.uv.deps import add_default_groups
        from usethis._integrations.uv.toml import UVTOMLManager
        from usethis._test import change_cwd

        (tmp_path / "uv.toml").touch()

        # Act
        with change_cwd(tmp_path), files_manager():
            add_default_groups(["test"])

        # Assert
        with change_cwd(tmp_path), UVTOMLManager():
            assert (
                (tmp_path / "uv.toml").read_text()
                == """\
default-groups = ["test"]
"""
            )


class TestGetDefaultGroups:
    def test_empty_pyproject_toml(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import get_default_groups
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").touch()

        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Act
            result = get_default_groups()

            # Assert
            assert result == []

    def test_invalid_default_groups(self, tmp_path: Path):
        # Arrange
        from usethis._integrations.file.pyproject_toml.io_ import PyprojectTOMLManager
        from usethis._integrations.uv.deps import get_default_groups
        from usethis._test import change_cwd

        (tmp_path / "pyproject.toml").write_text("""\
[tool.uv]
default-groups = "not a list"
""")

        with change_cwd(tmp_path), PyprojectTOMLManager():
            # Act
            result = get_default_groups()

            # Assert
            assert result == []

    def test_uv_toml(self, tmp_path: Path):
        # Arrange
        from usethis._config_file import files_manager
        from usethis._integrations.uv.deps import get_default_groups
        from usethis._test import change_cwd

        (tmp_path / "uv.toml").write_text("""\
default-groups = ["test"]
""")
        # Even if the pyproject.toml disagrees!
        (tmp_path / "pyproject.toml").write_text("""\
[tool.uv]
default-groups = ["doc"]
""")

        with change_cwd(tmp_path), files_manager():
            # Act
            result = get_default_groups()

            # Assert
            assert result == ["test"]

    def test_uv_toml_empty(self, tmp_path: Path):
        # Arrange
        from usethis._config_file import files_manager
        from usethis._integrations.uv.deps import get_default_groups
        from usethis._test import change_cwd

        (tmp_path / "uv.toml").touch()
        (tmp_path / "pyproject.toml").write_text("""\
[tool.uv]
default-groups = ["doc"]
""")

        with change_cwd(tmp_path), files_manager():
            # Act
            result = get_default_groups()

            # Assert
            assert result == []
