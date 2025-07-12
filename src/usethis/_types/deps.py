from pydantic import BaseModel


class Dependency(BaseModel):
    name: str
    extras: frozenset[str] = frozenset()

    def __str__(self) -> str:
        extras = sorted(self.extras or set())
        return self.name + "".join(f"[{extra}]" for extra in extras)

    def __hash__(self) -> int:
        return hash((self.__class__.__name__, self.name, self.extras))
