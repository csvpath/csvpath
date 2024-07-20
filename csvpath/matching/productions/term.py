from typing import Any
from csvpath.matching.productions.matchable import Matchable


class Term(Matchable):
    def __str__(self) -> str:
        return f"""{self.__class__}: {self.value} """

    def reset(self) -> None:
        super().reset()

    def to_value(self, *, skip=[]) -> Any:
        if isinstance(self.value, str) and self.value[0] == '"':
            self.value = self.value[1:]
        if isinstance(self.value, str) and self.value[len(self.value) - 1] == '"':
            self.value = self.value[0 : len(self.value) - 1]
        v = self.value
        return v
