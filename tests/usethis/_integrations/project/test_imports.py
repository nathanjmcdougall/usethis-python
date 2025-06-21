from pathlib import Path

import pytest


class TestLayeredArchitecture:
    class TestModuleCount:
        def test_mix(self):
            # Arrange

            from usethis._integrations.project.imports import LayeredArchitecture

            arch = LayeredArchitecture(
                layers=[{"a"}, {"b", "c"}],
                excluded={"d", "e"},
            )

            # Act
            count = arch.module_count()

            # Assert
            assert count == 3

        def test_excluded(self):
            # Arrange

            from usethis._integrations.project.imports import LayeredArchitecture

            arch = LayeredArchitecture(
                layers=[{"a"}, {"b", "c"}],
                excluded={"d", "e"},
            )

            # Act
            count = arch.module_count(include_excluded=True)

            # Assert
            assert count == 5


class TestGetLayeredArchitectures:
    def test_five(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Arrange

        from usethis._integrations.project.imports import (
            LayeredArchitecture,
            get_layered_architectures,
        )
        from usethis._test import change_cwd

        (tmp_path / "salut").mkdir()
        (tmp_path / "salut" / "__init__.py").touch()
        (tmp_path / "salut" / "a").mkdir()
        (tmp_path / "salut" / "a" / "__init__.py").touch()
        (tmp_path / "salut" / "b.py").write_text("""\
import salut.a
""")
        (tmp_path / "salut" / "c.py").write_text("""\
import salut.a
import salut.b
""")
        (tmp_path / "salut" / "d").mkdir()
        (tmp_path / "salut" / "d" / "__init__.py").touch()
        (tmp_path / "salut" / "d" / "e.py").write_text("""\
import salut.a
import salut.b
import salut.d.f
""")
        (tmp_path / "salut" / "d" / "f.py").touch()

        monkeypatch.syspath_prepend(str(tmp_path))

        # Act
        with change_cwd(tmp_path):
            arch_by_module = get_layered_architectures("salut")

        # Assert
        assert isinstance(arch_by_module, dict)
        for arch in arch_by_module.values():
            assert isinstance(arch, LayeredArchitecture)
        assert len(arch_by_module) == 7
        assert arch_by_module["salut"].layers == [{"c", "d"}, {"b"}, {"a"}]
        assert arch_by_module["salut"].excluded == set()
        assert arch_by_module["salut.d"].layers == [{"e"}, {"f"}]
        assert arch_by_module["salut.d"].excluded == set()


class TestGetModuleLayeredArchitecture:
    def test_three(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Arrange

        from usethis._integrations.project.imports import (
            LayeredArchitecture,
            _get_graph,
            _get_module_layered_architecture,
        )
        from usethis._test import change_cwd

        (tmp_path / "salut").mkdir()
        (tmp_path / "salut" / "__init__.py").touch()
        (tmp_path / "salut" / "a.py").touch()
        (tmp_path / "salut" / "b.py").write_text("""\
import salut.a
""")
        (tmp_path / "salut" / "c.py").write_text("""\
import salut.a
import salut.b
""")

        monkeypatch.syspath_prepend(str(tmp_path))

        # Act
        with change_cwd(tmp_path):
            graph = _get_graph("salut")
            arch = _get_module_layered_architecture("salut", graph=graph)

        # Assert
        assert isinstance(arch, LayeredArchitecture)
        assert arch.layers == [{"c"}, {"b"}, {"a"}]
        assert arch.excluded == set()

    def test_independent(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Arrange

        from usethis._integrations.project.imports import (
            LayeredArchitecture,
            _get_graph,
            _get_module_layered_architecture,
        )
        from usethis._test import change_cwd

        (tmp_path / "salut").mkdir()
        (tmp_path / "salut" / "__init__.py").touch()
        (tmp_path / "salut" / "a.py").touch()
        (tmp_path / "salut" / "b.py").touch()

        monkeypatch.syspath_prepend(str(tmp_path))

        # Act
        with change_cwd(tmp_path):
            graph = _get_graph("salut")
            arch = _get_module_layered_architecture("salut", graph=graph)

        # Assert
        assert isinstance(arch, LayeredArchitecture)
        assert arch.layers == [{"a", "b"}]
        assert arch.excluded == set()

    def test_cyclic(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Arrange

        from usethis._integrations.project.imports import (
            LayeredArchitecture,
            _get_graph,
            _get_module_layered_architecture,
        )
        from usethis._test import change_cwd

        (tmp_path / "salut").mkdir()
        (tmp_path / "salut" / "__init__.py").touch()
        (tmp_path / "salut" / "a.py").write_text("""\
import salut.b
""")
        (tmp_path / "salut" / "b.py").write_text("""\
import salut.a
""")

        monkeypatch.syspath_prepend(str(tmp_path))

        # Act
        with change_cwd(tmp_path):
            graph = _get_graph("salut")
            arch = _get_module_layered_architecture("salut", graph=graph)

        # Assert
        assert isinstance(arch, LayeredArchitecture)
        assert arch.layers == []
        assert arch.excluded == {"a", "b"}

    def test_bottom_heavy(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # For a given package structure, there are multiple possible layered
        # architectures it will comply with. We would prefer one which is "bottom heavy",
        # i.e. one or modules which depend on many independent modules, rather than
        # many independent modules which depend on one module.
        # Consider the following package structure:
        #
        # A
        # └── D
        # └── E
        #     ├── F
        #     └── G
        # B
        # C
        #
        # The following layered architectures are possible:
        # > {"B", "C", "F", "G"}, {"D", "E"}, {"A"}
        # > {'C', 'D', 'B', 'G', 'F'}, {'E'}, {'A'}
        # But this is bottom-heavy, and so preferred:
        # > {"F", "G"}, {"D", "E"}, {"A", "B", "C"}

        # Arrange

        from usethis._integrations.project.imports import (
            LayeredArchitecture,
            _get_graph,
            _get_module_layered_architecture,
        )
        from usethis._test import change_cwd

        (tmp_path / "salut").mkdir()
        (tmp_path / "salut" / "__init__.py").touch()
        (tmp_path / "salut" / "a.py").touch()
        (tmp_path / "salut" / "b.py").touch()
        (tmp_path / "salut" / "c.py").touch()
        (tmp_path / "salut" / "d.py").write_text("""\
import salut.a
""")
        (tmp_path / "salut" / "e.py").write_text("""\
import salut.a
""")
        (tmp_path / "salut" / "f.py").write_text("""\
import salut.e
""")
        (tmp_path / "salut" / "g.py").write_text("""\
import salut.e
""")

        monkeypatch.syspath_prepend(str(tmp_path))

        # Act
        with change_cwd(tmp_path):
            graph = _get_graph("salut")
            arch = _get_module_layered_architecture("salut", graph=graph)

        # Assert
        assert isinstance(arch, LayeredArchitecture)
        assert arch.layers == [{"f", "g"}, {"d", "e"}, {"a", "b", "c"}]
        assert arch.excluded == set()


class TestGetChildDependencies:
    def test_three(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Arrange

        from usethis._integrations.project.imports import (
            _get_child_dependencies,
            _get_graph,
        )
        from usethis._test import change_cwd

        (tmp_path / "salut").mkdir()
        (tmp_path / "salut" / "__init__.py").touch()
        (tmp_path / "salut" / "a.py").touch()
        (tmp_path / "salut" / "b.py").write_text("""\
import salut.a
""")
        (tmp_path / "salut" / "c.py").write_text("""\
import salut.a
import salut.b
""")

        monkeypatch.syspath_prepend(str(tmp_path))

        # Act
        with change_cwd(tmp_path):
            graph = _get_graph("salut")
            deps_by_module = _get_child_dependencies("salut", graph=graph)

        # Assert
        assert deps_by_module == {
            "a": set(),
            "b": {"a"},
            "c": {"a", "b"},
        }

    def test_two(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Arrange

        from usethis._integrations.project.imports import (
            _get_child_dependencies,
            _get_graph,
        )
        from usethis._test import change_cwd

        (tmp_path / "salut").mkdir()
        (tmp_path / "salut" / "__init__.py").touch()
        (tmp_path / "salut" / "a.py").touch()
        (tmp_path / "salut" / "b.py").write_text("""\
import salut.a
""")

        monkeypatch.syspath_prepend(str(tmp_path))

        # Act
        with change_cwd(tmp_path):
            graph = _get_graph("salut")
            deps_by_module = _get_child_dependencies("salut", graph=graph)

        # Assert
        assert deps_by_module == {
            "a": set(),
            "b": {"a"},
        }

    def test_none(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Arrange

        from usethis._integrations.project.imports import (
            _get_child_dependencies,
            _get_graph,
        )
        from usethis._test import change_cwd

        (tmp_path / "salut").mkdir()
        (tmp_path / "salut" / "__init__.py").touch()

        monkeypatch.syspath_prepend(str(tmp_path))

        # Act
        with change_cwd(tmp_path):
            graph = _get_graph("salut")
            deps_by_module = _get_child_dependencies("salut", graph=graph)

        # Assert
        assert deps_by_module == {}

    def test_submodule_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Arrange

        from usethis._integrations.project.imports import (
            _get_child_dependencies,
            _get_graph,
        )
        from usethis._test import change_cwd

        (tmp_path / "salut").mkdir()
        (tmp_path / "salut" / "__init__.py").touch()
        (tmp_path / "salut" / "a.py").touch()
        (tmp_path / "salut" / "b.py").write_text("""\
import salut.a
""")

        monkeypatch.syspath_prepend(str(tmp_path))

        # Act
        with change_cwd(tmp_path):
            graph = _get_graph("salut")
            deps_by_module = _get_child_dependencies("salut.a", graph=graph)

        # Assert
        assert deps_by_module == {}

    def test_submodule_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Arrange

        from usethis._integrations.project.imports import (
            _get_child_dependencies,
            _get_graph,
        )
        from usethis._test import change_cwd

        (tmp_path / "salut").mkdir()
        (tmp_path / "salut" / "__init__.py").touch()
        (tmp_path / "salut" / "a").mkdir()
        (tmp_path / "salut" / "a" / "__init__.py").touch()
        (tmp_path / "salut" / "a" / "b.py").touch()

        monkeypatch.syspath_prepend(str(tmp_path))

        # Act
        with change_cwd(tmp_path):
            graph = _get_graph("salut")
            deps_by_module = _get_child_dependencies("salut.a", graph=graph)

        # Assert
        assert deps_by_module == {"b": set()}


class TestFilterToSubmodule:
    def test_simple_case(self):
        # Arrange

        from usethis._integrations.project.imports import _filter_to_submodule

        modules = {"salut", "salut.a", "salut.b", "salut.c"}

        # Act
        filtered = _filter_to_submodule(modules, submodule="salut")

        # Assert
        assert filtered == {"a", "b", "c"}

    def test_no_submodule(self):
        # Arrange

        from usethis._integrations.project.imports import _filter_to_submodule

        modules = {"salut", "salut.a", "salut.b", "salut.c"}

        # Act
        filtered = _filter_to_submodule(modules, submodule="does_not_exist")

        # Assert
        assert filtered == set()

    def test_grandchild(self):
        # Arrange

        from usethis._integrations.project.imports import _filter_to_submodule

        modules = {"salut", "salut.a", "salut.b", "salut.c", "salut.a.d"}

        # Act
        filtered = _filter_to_submodule(modules, submodule="salut.a")

        # Assert
        assert filtered == {"d"}

    def test_child_with_children(self):
        # Arrange

        from usethis._integrations.project.imports import _filter_to_submodule

        modules = {"salut", "salut.a", "salut.b", "salut.c", "salut.a.d"}

        # Act
        filtered = _filter_to_submodule(modules, submodule="salut")

        # Assert
        assert filtered == {"a", "b", "c"}


class TestGetGraph:
    def test_type(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Arrange
        import grimp

        from usethis._integrations.project.imports import _get_graph
        from usethis._test import change_cwd

        (tmp_path / "salut").mkdir()
        (tmp_path / "salut" / "__init__.py").touch()

        monkeypatch.syspath_prepend(str(tmp_path))

        # Act
        with change_cwd(tmp_path):
            graph = _get_graph("salut")

        # Assert
        assert isinstance(graph, grimp.ImportGraph)

    def test_self(self):
        # Arrange
        import grimp

        from usethis._integrations.project.imports import _get_graph

        # Act
        graph = _get_graph("usethis")

        # Assert
        assert isinstance(graph, grimp.ImportGraph)

    def test_does_not_exist(self):
        # Arrange

        from usethis._integrations.project.errors import ImportGraphBuildFailedError
        from usethis._integrations.project.imports import _get_graph

        # Act, Assert
        with pytest.raises(ImportGraphBuildFailedError):
            _get_graph("does_not_exist")

    def test_not_top_level(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Arrange

        from usethis._integrations.project.errors import ImportGraphBuildFailedError
        from usethis._integrations.project.imports import _get_graph
        from usethis._test import change_cwd

        (tmp_path / "salut").mkdir()
        (tmp_path / "salut" / "__init__.py").touch()
        (tmp_path / "salut" / "a.py").touch()

        monkeypatch.syspath_prepend(str(tmp_path))

        # Act, Assert
        with (
            change_cwd(tmp_path),
            pytest.raises(ImportGraphBuildFailedError),
        ):
            _get_graph("salut.a")

    def test_not_package(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Arrange

        from usethis._integrations.project.errors import ImportGraphBuildFailedError
        from usethis._integrations.project.imports import _get_graph
        from usethis._test import change_cwd

        (tmp_path / "salut.py").touch()

        monkeypatch.syspath_prepend(str(tmp_path))

        # Act, Assert
        with (
            change_cwd(tmp_path),
            pytest.raises(ImportGraphBuildFailedError),
        ):
            _get_graph("salut.a")

    def test_exists_not_on_path(self, tmp_path: Path):
        # Arrange

        from usethis._integrations.project.errors import ImportGraphBuildFailedError
        from usethis._integrations.project.imports import _get_graph
        from usethis._test import change_cwd

        # N.B. we use the name 'different_name' since generating the graph in other
        # tests has the side-effect of importing the module, which persists between
        # tests.
        (tmp_path / "different_name.py").touch()

        # Act, Assert
        with (
            change_cwd(tmp_path),
            pytest.raises(
                ImportGraphBuildFailedError,
                match="__path__ attribute not found on 'different_name'",
            ),
        ):
            _get_graph("different_name.a")

    def test_namespace_package_top_level(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange

        from usethis._integrations.project.imports import _get_graph
        from usethis._test import change_cwd
        from usethis.errors import UsethisError

        (tmp_path / "abientot").mkdir()
        (tmp_path / "abientot" / "a").mkdir()
        (tmp_path / "abientot" / "a" / "__init__.py").touch()
        (tmp_path / "abientot" / "a" / "b.py").touch()

        monkeypatch.syspath_prepend(str(tmp_path))

        # Act, Assert
        with change_cwd(tmp_path), pytest.raises(UsethisError):
            _get_graph("abientot")

    def test_namespace_package_portion(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange
        import grimp

        from usethis._integrations.project.imports import _get_graph
        from usethis._test import change_cwd

        (tmp_path / "merci").mkdir()
        (tmp_path / "merci" / "a").mkdir()
        (tmp_path / "merci" / "a" / "__init__.py").touch()
        (tmp_path / "merci" / "a" / "b.py").touch()

        monkeypatch.syspath_prepend(str(tmp_path))

        # Act
        with change_cwd(tmp_path):
            graph = _get_graph("merci.a")

        # Assert
        assert isinstance(graph, grimp.ImportGraph)
