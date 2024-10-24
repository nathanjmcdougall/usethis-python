from typing import Any

from pydantic import BaseModel


class PyProjectConfig(BaseModel):
    id_keys: list[str]
    main_contents: dict[str, Any]