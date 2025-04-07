import grimp
import grimp.application
import grimp.application.config
import grimp.exceptions
from pydantic import BaseModel

from usethis._integrations.project.errors import ImportGraphBuildFailedError


class LayeredArchitecture(BaseModel):
    layers: list[set[str]]
    excluded: set[str] = set()

    def module_count(self, include_excluded: bool = False) -> int:
        """Count the number of modules in the architecture."""
        count = sum(len(layer) for layer in self.layers)
        if include_excluded:
            count += len(self.excluded)
        return count


def get_layered_architectures(pkg_name: str) -> dict[str, LayeredArchitecture]:
    """Get the suggested layers for a package.

    This is intended to inform the basis of a layer contract.

    Reference:
        https://import-linter.readthedocs.io/en/stable/contract_types.html#layers

    Args:
        pkg_name: The name of the package.

    Returns:
        A dictionary mapping module names to their layered architecture.
    """
    graph = _get_graph(pkg_name)

    arch_by_module = {}

    for module in sorted(graph.modules):
        arch = _get_module_layered_architecture(module, graph=graph)
        arch_by_module[module] = arch

    return arch_by_module


def _get_module_layered_architecture(
    module: str, *, graph: grimp.ImportGraph
) -> LayeredArchitecture:
    deps_by_module = _get_child_dependencies(module, graph=graph)

    layered = set()
    layers = []

    for _ in range(len(deps_by_module)):
        # Form a layer: cycle through all siblings. For ones with no deps, add them
        # to the layer and ignore them in the next iteration.

        layer = set()
        for m, deps in deps_by_module.items():
            if m in layered:
                continue

            unlayered_deps = deps - layered - {m}
            if not unlayered_deps:
                layer.add(m)

        if not layer:
            break

        layers.append(layer)
        layered.update(layer)

    excluded = set()
    for m in deps_by_module:
        if m not in layered:
            excluded.add(m)

    return LayeredArchitecture(
        layers=list(reversed(layers)),
        excluded=excluded,
    )


def _get_child_dependencies(
    module: str, *, graph: grimp.ImportGraph
) -> dict[str, set[str]]:
    """For each child submodule, give a set of the sibling submodules it depends on.

    For example, let's say we have `c` which depends on `a`, and `b` depends on `a`.
    `a` does not depend on anything, and `c` depends on `a` through `b`. Then the
    function will return:

    ```
    {
        "a": set(),
        "b": {"a"},
        "c": {"a", "b"},
    }
    ```
    """
    children = sorted(graph.find_children(module))

    deps_by_module = {}
    for child in children:
        downstreams = graph.find_upstream_modules(module=child, as_package=True)
        downstreams = _filter_to_submodule(downstreams, submodule=module)

        deps_by_module[_narrow_to_submodule(child, submodule=module)] = downstreams

    return deps_by_module


def _filter_to_submodule(modules: set[str], *, submodule: str) -> set[str]:
    filtered = set()
    for module in modules:
        if module.startswith(submodule + "."):
            filtered.add(_narrow_to_submodule(module, submodule=submodule))

    return filtered


def _narrow_to_submodule(module: str, *, submodule: str) -> str:
    return module.removeprefix(submodule + ".").split(".")[0]


def _get_graph(pkg_name: str) -> grimp.ImportGraph:
    try:
        graph = grimp.build_graph(pkg_name, cache_dir=None)
    except ValueError as err:
        raise ImportGraphBuildFailedError(err) from None
    except (ModuleNotFoundError, grimp.exceptions.NamespacePackageEncountered) as err:
        raise ImportGraphBuildFailedError(err) from None
    except grimp.exceptions.NotATopLevelModule:
        msg = f"Module {pkg_name} is not a top-level module, cannot build graph."
        raise ImportGraphBuildFailedError(msg) from None
    return graph
