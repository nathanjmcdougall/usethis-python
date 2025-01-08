from typing import assert_never
from uuid import uuid4

import usethis._pipeweld.containers
from usethis._integrations.bitbucket.dump import bitbucket_fancy_dump
from usethis._integrations.bitbucket.errors import UnexpectedImportPipelineError
from usethis._integrations.bitbucket.io import (
    BitbucketPipelinesYAMLDocument,
    edit_bitbucket_pipelines_yaml,
)
from usethis._integrations.bitbucket.schema import (
    ImportPipeline,
    Items,
    ParallelExpanded,
    ParallelItem,
    ParallelSteps,
    Pipeline,
    Pipelines,
    PipelinesConfiguration,
    StageItem,
    Step,
    StepItem,
)
from usethis._integrations.bitbucket.schema_utils import step1tostep
from usethis._integrations.yaml.update import update_ruamel_yaml_map
from usethis._pipeweld.ops import Instruction


def get_pipeweld_step(step: Step) -> str:
    if step.name is not None:
        return step.name
    return step.model_dump_json()


# TODO reduce complexity and enable below ruff rule
def get_pipeweld_pipeline_from_default(  # noqa: PLR0912
    model: PipelinesConfiguration,
) -> usethis._pipeweld.containers.Series:
    if model.pipelines is None:
        model.pipelines = Pipelines()
    default = model.pipelines.default

    if default is None:
        items = []
    elif isinstance(default.root, ImportPipeline):
        msg = (
            "Cannot add step to default pipeline in 'bitbucket-pipelines.yml' because "
            "it is an import pipeline."
        )
        raise UnexpectedImportPipelineError(msg)
    else:
        items = default.root.root

    series = []
    for item in items:
        if isinstance(item, StepItem):
            series.append(get_pipeweld_step(item.step))
        elif isinstance(item, ParallelItem):
            parallel_steps: set[str] = set()

            if item.parallel is not None:
                if isinstance(item.parallel.root, ParallelSteps):
                    step_items = item.parallel.root.root
                elif isinstance(item.parallel.root, ParallelExpanded):
                    step_items = item.parallel.root.steps.root
                else:
                    assert_never(item.parallel.root)

                for step_item in step_items:
                    parallel_steps.add(get_pipeweld_step(step_item.step))

            series.append(
                usethis._pipeweld.containers.Parallel(frozenset(parallel_steps))
            )
        elif isinstance(item, StageItem):
            depgroup_steps: list[str] = []

            if item.stage is not None:
                if item.stage.name is not None:
                    name = item.stage.name
                else:
                    name = str(f"Unnamed Stage {uuid4()}")

                for step in item.stage.steps:
                    depgroup_steps.append(get_pipeweld_step(step1tostep(step)))
            else:
                name = str(f"Unnamed Stage {uuid4()}")

            series.append(
                usethis._pipeweld.containers.DepGroup(
                    series=usethis._pipeweld.containers.series(*depgroup_steps),
                    config_group=name,
                )
            )
        else:
            assert_never(item)

    return usethis._pipeweld.containers.series(*series)


def apply_pipeweld_instruction(instruction: Instruction, *, new_step: Step) -> None:
    with edit_bitbucket_pipelines_yaml() as doc:
        apply_pipeweld_instruction_via_doc(instruction, doc=doc, new_step=new_step)
        dump = bitbucket_fancy_dump(doc.model, reference=doc.content)
        update_ruamel_yaml_map(doc.content, dump, preserve_comments=True)


# TODO: reduce complexity and enable ruff rules
def apply_pipeweld_instruction_via_doc(  # noqa: PLR0912
    instruction: Instruction,
    *,
    new_step: Step,
    doc: BitbucketPipelinesYAMLDocument,
) -> None:
    if get_pipeweld_step(new_step) != instruction.step:
        # N.B. This doesn't currently handle moving existing steps
        return

    if doc.model.pipelines is None:
        doc.model.pipelines = Pipelines()

    pipelines = doc.model.pipelines
    default = pipelines.default

    if default is None:
        items = []
    elif isinstance(default.root, ImportPipeline):
        msg = (
            f"Cannot add step '{new_step.name}' to default pipeline in "
            f"'bitbucket-pipelines.yml' because it is an import pipeline."
        )
        raise UnexpectedImportPipelineError(msg)
    else:
        items = default.root.root

    if instruction.after is None:
        items.insert(0, StepItem(step=new_step))
    else:
        has_inserted = False
        for item in items:
            if isinstance(item, StepItem):
                if get_pipeweld_step(item.step) == instruction.after:
                    # N.B. This doesn't currently handle InsertParallel properly
                    items.insert(
                        items.index(item) + 1,
                        StepItem(step=new_step),
                    )
                    has_inserted = True
            elif isinstance(item, ParallelItem):
                if isinstance(item.parallel.root, ParallelSteps):
                    step_items = item.parallel.root.root
                elif isinstance(item.parallel.root, ParallelExpanded):
                    step_items = item.parallel.root.steps.root
                else:
                    assert_never(item.parallel.root)

                for step_item in step_items:
                    if get_pipeweld_step(step_item.step) == instruction.after:
                        # N.B. This doesn't currently handle InsertParallel properly
                        items.insert(
                            items.index(item) + 1,
                            StepItem(step=new_step),
                        )
                        has_inserted = True
                        break
            elif isinstance(item, StageItem):
                step1s = item.stage.steps.copy()

                for step1 in step1s:
                    step = step1tostep(step1)

                    if get_pipeweld_step(step) == instruction.after:
                        # N.B. This doesn't currently handle InsertParallel properly
                        items.insert(
                            items.index(item) + 1,
                            StepItem(step=new_step),
                        )
                        has_inserted = True
            else:
                assert_never(item)

            if has_inserted:
                break

    if default is None and items:
        pipelines.default = Pipeline(Items(items))
