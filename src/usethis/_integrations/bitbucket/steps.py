from functools import singledispatch
from pathlib import Path
from typing import assert_never

from ruamel.yaml.anchor import Anchor
from ruamel.yaml.comments import CommentedSeq
from ruamel.yaml.scalarstring import LiteralScalarString

import usethis._pipeweld.func
from usethis._console import box_print, tick_print
from usethis._integrations.bitbucket.anchor import ScriptItemAnchor, ScriptItemName
from usethis._integrations.bitbucket.cache import add_caches
from usethis._integrations.bitbucket.dump import bitbucket_fancy_dump
from usethis._integrations.bitbucket.errors import UnexpectedImportPipelineError
from usethis._integrations.bitbucket.io import (
    BitbucketPipelinesYAMLDocument,
    edit_bitbucket_pipelines_yaml,
)
from usethis._integrations.bitbucket.pipeweld import (
    apply_pipeweld_instruction,
    get_pipeweld_pipeline_from_default,
    get_pipeweld_step,
)
from usethis._integrations.bitbucket.schema import (
    CachePath,
    Definitions,
    ImportPipeline,
    Parallel,
    ParallelExpanded,
    ParallelItem,
    ParallelSteps,
    Pipeline,
    Script,
    StageItem,
    Step,
    StepItem,
)
from usethis._integrations.bitbucket.schema_utils import step1tostep
from usethis._integrations.pyproject.requires_python import _ALL_MAJOR_VERSIONS
from usethis._integrations.yaml.update import update_ruamel_yaml_map

_CACHE_LOOKUP = {
    "uv": CachePath("~/.cache/uv"),
    "pre-commit": CachePath("~/.cache/pre-commit"),
}

# TODO shold consider adding all "Run tests with Python 3.x" steps to run in
# parallel
_STEP_ORDER = [
    "Run pre-commit hooks",
    *[f"Run tests with Python 3.{maj}" for maj in _ALL_MAJOR_VERSIONS],
]

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


def add_step_in_default(step: Step) -> None:
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
        if _steps_are_equivalent(existing_step, step):
            return

    add_step_caches(step)

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
    # TODO test messages to user about this.
    placeholder = _get_placeholder_step()
    if not _steps_are_equivalent(placeholder, step):
        # Only remove the placeholder if it hasn't already been added.
        remove_step_from_default(placeholder)


# TODO reduce the complexity of the below function and enable the ruff rule
def _add_step_in_default_via_doc(
    step: Step, *, doc: BitbucketPipelinesYAMLDocument
) -> None:
    if step.name == _PLACEHOLDER_NAME:
        tick_print(
            "Adding placeholder step to default pipeline in 'bitbucket-pipelines.yml'."
        )
    else:
        tick_print(
            f"Adding step '{step.name}' to default pipeline in "
            f"'bitbucket-pipelines.yml'."
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

                # N.B. when we add the definition, we are relying on this being
                # an append
                # TODO revisit this - maybe we should add alphabetically.
                script_items.append(script_item)
                script_items = CommentedSeq(script_items)
            else:
                # Otherwise, if the anchor is already defined, we need to use the
                # reference
                script_item = defined_script_item_by_name[script_item.name]

            step.script.root[idx] = script_item

    # N.B. if the step is unrecognized, it will go at the end.
    prerequisites: set[str] = set()
    for step_name in _STEP_ORDER:
        if step_name == step.name:
            break
        prerequisites.add(step_name)

    weld_result = usethis._pipeweld.func.add(
        pipeline=get_pipeweld_pipeline_from_default(doc.model),
        step=get_pipeweld_step(step),
        prerequisites=prerequisites,
    )
    for instruction in weld_result.instructions:
        apply_pipeweld_instruction(instruction=instruction, new_step=step, doc=doc)

    # TODO need to tell the user to review the pipeline, it might be wrong. Test
    # associated message. This is mostly the case if there are unrecognized
    # aspects detected, no need if we are starting from scratch and/or fully supported
    # hooks are already present. And some thought needed around whether we can just take
    # for granted that things always need review.


# TODO refactor the below to reduce complexity and enable the ruff rules
def remove_step_from_default(step: Step) -> None:  # noqa: PLR0912, PLR0915
    """Remove a step from the default pipeline in the Bitbucket Pipelines configuration.

    If the default pipeline does not exist, or the step is not found, nothing happens.
    """
    if not (Path.cwd() / "bitbucket-pipelines.yml").exists():
        return

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

        new_items: list[StepItem | ParallelItem | StageItem] = []
        for item in items:
            if isinstance(item, ParallelItem):
                if item.parallel is None:
                    continue

                par = item.parallel.root

                if isinstance(par, ParallelSteps):
                    step_items = par.root
                elif isinstance(par, ParallelExpanded):
                    step_items = par.steps.root
                else:
                    assert_never(par)

                new_step_items: list[StepItem] = []
                for step_item in step_items:
                    if step_item.step is None:
                        continue

                    if _steps_are_equivalent(step_item.step, step):
                        continue

                    new_step_items.append(step_item)

                if len(new_step_items) == 0:
                    continue
                elif len(new_step_items) == 1 and len(step_items) != 1:
                    # Collapse the parallel step down to a single step, but only if
                    # it wasn't already a single step, in which case we'll leave it
                    # alone.
                    new_items.append(new_step_items[0])
                elif isinstance(par, ParallelSteps):
                    new_items.append(
                        ParallelItem(parallel=Parallel(ParallelSteps(new_step_items)))
                    )
                elif isinstance(par, ParallelExpanded):
                    par.steps = ParallelSteps(new_step_items)
                    new_items.append(ParallelItem(parallel=Parallel(par)))
                else:
                    assert_never(par)
            elif isinstance(item, StageItem):
                if item.stage is None:
                    continue

                step1s = item.stage.steps

                new_step1s = []
                for step1 in step1s:
                    if step1.step is None:
                        continue

                    if _steps_are_equivalent(step1tostep(step1), step):
                        continue

                    new_step1s.append(step1)

                if len(new_step1s) == 0:
                    continue

                new_stage = item.stage.model_copy()
                new_stage.steps = new_step1s
                new_items.append(StageItem(stage=new_stage))
            elif isinstance(item, StepItem):
                if item.step is None:
                    continue

                if _steps_are_equivalent(item.step, step):
                    continue

                new_items.append(item)
            else:
                assert_never(item)
        pipeline.root.root = new_items

        if len(new_items) == 0:
            _add_step_in_default_via_doc(_get_placeholder_step(), doc=doc)

        dump = bitbucket_fancy_dump(doc.model, reference=doc.content)
        update_ruamel_yaml_map(doc.content, dump, preserve_comments=True)


def add_step_caches(step: Step) -> None:
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
        add_caches(cache_by_name)


def _steps_are_equivalent(step1: Step | None, step2: Step) -> bool:
    if step1 is None:
        return False

    # Same name
    if step1.name == step2.name:
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
    if not (Path.cwd() / "bitbucket-pipelines.yml").exists():
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
    if item.step is None:
        return []

    return [item.step]


@get_steps_in_pipeline_item.register(ParallelItem)
def _(item: ParallelItem) -> list[Step]:
    if item.parallel is None:
        return []

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
    if item.stage is None:
        return []

    step1s = item.stage.steps

    steps = [step1tostep(step1) for step1 in step1s if step1.step is not None]

    return steps


def add_placeholder_step_in_default() -> None:
    add_step_in_default(_get_placeholder_step())
    box_print("Remove the placeholder pipeline step in 'bitbucket-pipelines.yml'.")
    box_print("Replace it with your own pipeline steps.")
    box_print("Alternatively, use 'usethis tool' to add other tools and their steps.")


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


# TODO should test we are not double-defining an anchor with one defined elsewhere in
# the file. We should forbid some anchor names from being defined outside of the context
# we expect them.
# Alternatively, we could just assume that if it has the same name, it's the same anchor.
# This would probably be better in terms of not needing to hard-fail but it might be
# a bit dodgy since the anchor might refer to a different kind of object, and hence give
# invalid results. This needs some thought. Here is a draft of a function to traverse to
# find all anchors.
# ruff: noqa: ERA001
# def find_anchors(yaml_content):
#     yaml = YAML()
#     data = yaml.load(yaml_content)
#     anchors = []

#     def extract_anchors(node):
#         if isinstance(node, dict):
#             for key, value in node.items():
#                 if isinstance(key, Anchor):
#                     anchors.append(key.anchor)
#                 extract_anchors(value)
#         elif isinstance(node, list):
#             for item in node:
#                 extract_anchors(item)
#         elif hasattr(node, 'anchor') and node.anchor.value is not None:
#             anchors.append(node.anchor.value)

#     extract_anchors(data)
#     return anchors
