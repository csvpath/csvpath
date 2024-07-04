from typing import Any
from csvpath.matching.productions.expression import Matchable

class Term(Matchable):


    def __str__(self) -> str:
        return f"""{self.__class__}: {self.value} """

    def to_value(self, *, skip=[]) -> Any:
        v = self.value
        return v


