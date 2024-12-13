from pydantic import BaseModel

from usethis._integrations.bitbucket.schema import (
    PipelinesConfiguration,
    Step,
    Step2,
    StepBase,
)
from usethis._integrations.pydantic.dump import ModelRepresentation, fancy_model_dump

ORDER_BY_CLS: dict[type[BaseModel], list[str]] = {
    PipelinesConfiguration: ["image", "clone", "definitions"],
    StepBase: ["name", "caches", "script"],
    Step: ["name", "caches", "script"],
    Step2: ["name", "caches", "script"],
}


def bitbucket_fancy_dump(
    config: PipelinesConfiguration, *, reference: ModelRepresentation | None = None
) -> dict[str, ModelRepresentation]:
    dump = fancy_model_dump(config, reference=reference, order_by_cls=ORDER_BY_CLS)

    if not isinstance(dump, dict):
        name = f"{PipelinesConfiguration=}".split("=")[0]
        msg = (
            f"Invalid '{name}' representation when dumping; expected dict, got "
            f"{type(dump)}"
        )
        raise TypeError(msg)

    return dump
