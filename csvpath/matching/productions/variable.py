from typing import Any
from csvpath.matching.productions.expression import Matchable

class Variable(Matchable):


    def __str__(self) -> str:
        return f"""{self.__class__}: {self.name}"""

    def to_value(self, *, skip=[]) -> Any:
        v = self.matcher.get_variable(self.name)
        return v


