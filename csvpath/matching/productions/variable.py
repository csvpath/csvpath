from typing import Any
from csvpath.matching.productions.expression import Matchable

class Variable(Matchable):


    def __str__(self) -> str:
        return f"""{self.__class__}: {self.name}"""

    def to_value(self, *, skip=[]) -> Any:
        if not self.value:
            self.value = self.matcher.get_variable(self.name)
        return self.value


