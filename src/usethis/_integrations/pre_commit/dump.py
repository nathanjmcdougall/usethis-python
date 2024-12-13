from pydantic import BaseModel

from usethis._integrations.pre_commit.schema import (
    JsonSchemaForPreCommitConfigYaml,
)
from usethis._integrations.pydantic.dump import ModelRepresentation, fancy_model_dump

ORDER_BY_CLS: dict[type[BaseModel], list[str]] = {}


def precommit_fancy_dump(
    config: JsonSchemaForPreCommitConfigYaml, *, reference: ModelRepresentation
) -> dict[str, ModelRepresentation]:
    dump = fancy_model_dump(config, reference=reference, order_by_cls=ORDER_BY_CLS)

    if not isinstance(dump, dict):
        name = f"{JsonSchemaForPreCommitConfigYaml=}".split("=")[0]
        msg = (
            f"Invalid '{name}' representation when dumping; expected dict, got "
            f"{type(dump)}"
        )
        raise TypeError(msg)

    return dump
