from __future__ import annotations

from functools import singledispatch
from typing import TYPE_CHECKING

from ruamel.yaml.comments import CommentedSeq
from ruamel.yaml.scalarstring import LiteralScalarString
from typing_extensions import assert_never

import usethis._pipeweld.func
from usethis._config import usethis_config
from usethis._console import box_print, tick_print
from usethis._integrations.ci.bitbucket.anchor import ScriptItemAnchor
from usethis._integrations.ci.bitbucket.cache import _add_caches_via_doc, remove_cache
from usethis._integrations.ci.bitbucket.dump import bitbucket_fancy_dump
from usethis._integrations.ci.bitbucket.errors import UnexpectedImportPipelineError
from usethis._integrations.ci.bitbucket.io_ import edit_bitbucket_pipelines_yaml
from usethis._integrations.ci.bitbucket.pipeweld import (
    apply_pipeweld_instruction_via_doc,
    get_pipeweld_pipeline_from_default,
    get_pipeweld_step,
)
from usethis._integrations.ci.bitbucket.schema import (
    CachePath,
    Definitions,
    ImportPipeline,
    Parallel,
    ParallelExpanded,
    ParallelItem,
    ParallelSteps,
    Script,
    StageItem,
    Step,
    StepItem,
)
from usethis._integrations.ci.bitbucket.schema_utils import step1tostep
from usethis._integrations.file.yaml.update import update_ruamel_yaml_map
from usethis._integrations.uv.python import get_supported_major_python_versions

if TYPE_CHECKING:
    from ruamel.yaml.anchor import Anchor

    from usethis._integrations.ci.bitbucket.anchor import ScriptItemName
    from usethis._integrations.ci.bitbucket.io_ import BitbucketPipelinesYAMLDocument
    from usethis._integrations.ci.bitbucket.schema import Pipeline

_CACHE_LOOKUP = {
    "uv": CachePath("~/.cache/uv"),
    "pre-commit": CachePath("~/.cache/pre-commit"),
}


_PLACEHOLDER_NAME = "Placeholder - add your own steps!"

_SCRIPT_ITEM_LOOKUP: dict[ScriptItemName, LiteralScalarString] = {
    "install-uv": LiteralScalarString("""\
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
export UV_LINK_MODE=copy
uv --version
""")
}
for name, script_item in _SCRIPT_ITEM_LOOKUP.items():
    script_item.yaml_set_anchor(value=name, always_dump=True)


def add_bitbucket_step_in_default(step: Step) -> None:
    try:
        existing_steps = get_steps_in_default()
    except UnexpectedImportPipelineError:
        msg = (
            f"Cannot add step '{step.name}' to default pipeline in "
            f"'bitbucket-pipelines.yml' because it is an import pipeline."
        )
        raise UnexpectedImportPipelineError(msg) from None

    # Early exit if the step already exists in some sense
    for existing_step in existing_steps:
        if bitbucket_steps_are_equivalent(existing_step, step):
            return

    # Add the step to the default pipeline
    with edit_bitbucket_pipelines_yaml() as doc:
        _add_step_in_default_via_doc(step, doc=doc)
        dump = bitbucket_fancy_dump(doc.model, reference=doc.content)
        update_ruamel_yaml_map(
            doc.content,
            dump,
            preserve_comments=True,
        )

    # Remove the placeholder step if it already exists
    placeholder = _get_placeholder_step()
    if not bitbucket_steps_are_equivalent(placeholder, step):
        # Only remove the placeholder if it hasn't already been added.
        remove_bitbucket_step_from_default(placeholder)


def _add_step_in_default_via_doc(
    step: Step, *, doc: BitbucketPipelinesYAMLDocument
) -> None:
    _add_step_caches_via_doc(step, doc=doc)

    if step.name != _PLACEHOLDER_NAME:
        # We need to selectively choose to report at a higher level.
        # It's not always notable that the placeholder is being added.
        tick_print(
            f"Adding '{step.name}' to default pipeline in 'bitbucket-pipelines.yml'."
        )

    config = doc.model

    step = step.model_copy(deep=True)

    # If the step uses an anchorized script definition, add it to the definitions
    # section
    for idx, script_item in enumerate(step.script.root):
        if isinstance(script_item, ScriptItemAnchor):
            # We've found an anchorized script definition...

            # Get the names of the anchors which are already defined in the file.
            defined_script_item_by_name = get_defined_script_items_via_doc(doc=doc)

            # If our anchor doesn't have a definition yet, we need to add it.
            if script_item.name not in defined_script_item_by_name:
                try:
                    script_item = _SCRIPT_ITEM_LOOKUP[script_item.name]
                except KeyError:
                    msg = f"Unrecognized script item anchor: {script_item.name}"
                    raise NotImplementedError(msg) from None

                if config.definitions is None:
                    config.definitions = Definitions()

                script_items = config.definitions.script_items

                if script_items is None:
                    script_items = CommentedSeq()
                    config.definitions.script_items = script_items

                # N.B. Once we support multiple different types of script items, we will
                # probably want to enforce a canonical order rather than just append.
                # See also anchor.py.
                script_items.append(script_item)
                script_items = CommentedSeq(script_items)
            else:
                # Otherwise, if the anchor is already defined, we need to use the
                # reference
                script_item = defined_script_item_by_name[script_item.name]

            step.script.root[idx] = script_item

    # If the step is unrecognized, it will go at the end.
    prerequisites: set[str] = set()

    # N.B. Currently, we are not accounting for parallelism, whereas all these steps
    # could be parallel potentially.
    # See https://github.com/usethis-python/usethis-python/issues/149
    maj_versions = get_supported_major_python_versions()
    step_order = [
        "Run pre-commit",
        # For these tools, sync them with the pre-commit removal logic
        "Run pyproject-fmt",
        "Run Ruff",
        "Run Ruff Formatter",
        "Run deptry",
        "Run Codespell",
        *[f"Test on 3.{maj_version}" for maj_version in maj_versions],
    ]
    for step_name in step_order:
        if step_name == step.name:
            break
        prerequisites.add(step_name)

    weld_result = usethis._pipeweld.func.Adder(
        pipeline=get_pipeweld_pipeline_from_default(doc.model),
        step=get_pipeweld_step(step),
        prerequisites=prerequisites,
    ).add()
    for instruction in weld_result.instructions:
        apply_pipeweld_instruction_via_doc(
            instruction=instruction, new_step=step, doc=doc
        )


def remove_bitbucket_step_from_default(step: Step) -> None:
    """Remove a step from the default pipeline in the Bitbucket Pipelines configuration.

    If the default pipeline does not exist, or the step is not found, nothing happens.
    """
    if not (usethis_config.cpd() / "bitbucket-pipelines.yml").exists():
        return

    if step.name == _PLACEHOLDER_NAME:
        pass  # We need to selectively choose to report at a higher level.
        # It's not always notable that the placeholder is being removed.
    else:
        tick_print(
            f"Removing '{step.name}' from default pipeline in 'bitbucket-pipelines.yml'."
        )

    with edit_bitbucket_pipelines_yaml() as doc:
        config = doc.model

        if config.pipelines is None:
            return

        if config.pipelines.default is None:
            return

        pipeline = config.pipelines.default

        if isinstance(pipeline.root, ImportPipeline):
            msg = "Cannot remove steps from an import pipeline."
            raise UnexpectedImportPipelineError(msg)

        items = pipeline.root.root

        # Iterate over the items. Any item that contains the step is censored to remove
        # references to the step. If the only thing in the item is the step, we get None
        new_items: list[StepItem | ParallelItem | StageItem] = []
        for item in items:
            new_item = _censor_step(item, step=step)
            if new_item is not None:
                new_items.append(new_item)
        pipeline.root.root = new_items

        if len(new_items) == 0:
            placeholder = _get_placeholder_step()
            _add_step_in_default_via_doc(placeholder, doc=doc)

        dump = bitbucket_fancy_dump(doc.model, reference=doc.content)
        update_ruamel_yaml_map(doc.content, dump, preserve_comments=True)

    if step.caches is not None:
        for cache in step.caches:
            if not is_cache_used(cache):
                remove_cache(cache)


@singledispatch
def _censor_step(
    item: StepItem | ParallelItem | StageItem, *, step: Step
) -> StepItem | ParallelItem | StageItem | None:
    """Censor a step from a pipeline item, with None if necessary."""
    raise NotImplementedError


@_censor_step.register(StepItem)
def _(item: StepItem, *, step: Step) -> StepItem | ParallelItem | StageItem | None:
    if bitbucket_steps_are_equivalent(item.step, step):
        return None
    return item


@_censor_step.register(ParallelItem)
def _(item: ParallelItem, *, step: Step) -> StepItem | ParallelItem | StageItem | None:
    par = item.parallel.root

    if isinstance(par, ParallelSteps):
        step_items = par.root
    elif isinstance(par, ParallelExpanded):
        step_items = par.steps.root
    else:
        assert_never(par)

    new_step_items: list[StepItem] = []
    for step_item in step_items:
        if bitbucket_steps_are_equivalent(step_item.step, step):
            continue
        new_step_items.append(step_item)

    if len(new_step_items) == 0:
        return None
    elif len(new_step_items) == 1 and len(step_items) != 1:
        return new_step_items[0]
    elif isinstance(par, ParallelSteps):
        return ParallelItem(parallel=Parallel(ParallelSteps(new_step_items)))
    elif isinstance(par, ParallelExpanded):
        par.steps = ParallelSteps(new_step_items)
        return ParallelItem(parallel=Parallel(par))
    else:
        assert_never(par)


@_censor_step.register(StageItem)
def _(item: StageItem, *, step: Step) -> StepItem | ParallelItem | StageItem | None:
    step1s = item.stage.steps

    new_step1s = []
    for step1 in step1s:
        if bitbucket_steps_are_equivalent(step1tostep(step1), step):
            continue
        new_step1s.append(step1)

    if len(new_step1s) == 0:
        return None

    new_stage = item.stage.model_copy()
    new_stage.steps = new_step1s
    return StageItem(stage=new_stage)


def is_cache_used(cache: str) -> bool:
    for step in get_steps_in_default():
        if step.caches is not None and cache in step.caches:
            return True

    return False


def _add_step_caches_via_doc(
    step: Step, *, doc: BitbucketPipelinesYAMLDocument
) -> None:
    if step.caches is not None:
        cache_by_name = {}
        for name in step.caches:
            try:
                cache = _CACHE_LOOKUP[name]
            except KeyError:
                msg = (
                    f"Unrecognized cache name '{name}' in step '{step.name}'. "
                    f"Supported caches are 'uv' and 'pre-commit'."
                )
                raise NotImplementedError(msg) from None
            cache_by_name[name] = cache
        _add_caches_via_doc(cache_by_name, doc=doc)


def bitbucket_steps_are_equivalent(step1: Step | None, step2: Step) -> bool:
    if step1 is None:
        return False

    # Same name
    if step1.name == step2.name:
        return True

    # Same name up to case differences
    if (
        isinstance(step1.name, str)
        and isinstance(step2.name, str)
        and step1.name.lower() == step2.name.lower()
    ):
        return True

    # Same contents, different name
    step1 = step1.model_copy()
    step1.name = step2.name
    return step1 == step2


def get_steps_in_default() -> list[Step]:
    """Get the steps in the default pipeline of the Bitbucket Pipelines configuration.

    If the default pipeline does not exist, an empty list is returned.

    Returns:
        The steps in the default pipeline.

    Raises:
        UnexpectedImportPipelineError: If the pipeline is an import pipeline.
    """
    if not (usethis_config.cpd() / "bitbucket-pipelines.yml").exists():
        return []

    with edit_bitbucket_pipelines_yaml() as doc:
        config = doc.model

    if config.pipelines is None:
        return []

    if config.pipelines.default is None:
        return []

    pipeline = config.pipelines.default

    return _get_steps_in_pipeline(pipeline)


def _get_steps_in_pipeline(pipeline: Pipeline) -> list[Step]:
    if isinstance(pipeline.root, ImportPipeline):
        msg = "Cannot retrieve steps from an import pipeline."
        raise UnexpectedImportPipelineError(msg)

    items = pipeline.root.root

    steps = []
    for item in items:
        steps.extend(get_steps_in_pipeline_item(item))

    return steps


@singledispatch
def get_steps_in_pipeline_item(item) -> list[Step]: ...


@get_steps_in_pipeline_item.register(StepItem)
def _(item: StepItem) -> list[Step]:
    return [item.step]


@get_steps_in_pipeline_item.register(ParallelItem)
def _(item: ParallelItem) -> list[Step]:
    _p = item.parallel.root
    if isinstance(_p, ParallelSteps):
        step_items = _p.root
    elif isinstance(_p, ParallelExpanded):
        step_items = _p.steps.root
    else:
        assert_never(_p)

    steps = [step_item.step for step_item in step_items if step_item.step is not None]
    return steps


@get_steps_in_pipeline_item.register(StageItem)
def _(item: StageItem) -> list[Step]:
    return [step1tostep(step1) for step1 in item.stage.steps if step1.step is not None]


def add_placeholder_step_in_default(report_placeholder: bool = True) -> None:
    add_bitbucket_step_in_default(_get_placeholder_step())

    if report_placeholder:
        tick_print(
            "Adding placeholder step to default pipeline in 'bitbucket-pipelines.yml'."
        )
        box_print("Remove the placeholder pipeline step in 'bitbucket-pipelines.yml'.")
        box_print("Replace it with your own pipeline steps.")
        box_print(
            "Alternatively, use 'usethis tool' to add other tools and their steps."
        )


def _get_placeholder_step() -> Step:
    return Step(
        name=_PLACEHOLDER_NAME,
        script=Script(
            [
                ScriptItemAnchor(name="install-uv"),
                "echo 'Hello, world!'",
            ]
        ),
        caches=["uv"],
    )


def get_defined_script_items_via_doc(
    doc: BitbucketPipelinesYAMLDocument,
) -> dict[str, str]:
    """These are the names of the anchors."""
    config = doc.model

    if config.definitions is None:
        return {}

    if config.definitions.script_items is None:
        return {}

    script_item_contents = doc.content["definitions"]["script_items"]

    script_anchor_by_name = {}
    for script_item_content in script_item_contents:
        if not isinstance(script_item_content, LiteralScalarString):
            # Not a script item definition
            continue

        anchor: Anchor = script_item_content.yaml_anchor()

        if anchor is None:
            # Unnamed definition, can't be used as an anchor
            continue

        anchor_name = anchor.value
        script_anchor_by_name[anchor_name] = script_item_content

    return script_anchor_by_name
