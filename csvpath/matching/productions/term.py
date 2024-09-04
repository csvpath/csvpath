from typing import Any
from csvpath.matching.productions.matchable import Matchable


class Term(Matchable):
    def __str__(self) -> str:
        return f"""{self._simple_class_name()}({self.value})"""

    def __init__(self, matcher, *, value: Any = None, name: str = None):
        if isinstance(value, str):
            value = value.lstrip('"').rstrip('"')
        super().__init__(matcher=matcher, name=name, value=value)

    def reset(self) -> None:
        super().reset()

    def to_value(self, *, skip=None) -> Any:
        return self.value
