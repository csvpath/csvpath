from typing import Any
from csvpath.matching.productions.expression import Matchable

class Header(Matchable):


    def __str__(self) -> str:
        return f"""{self.__class__}: {self.name} """

    def to_value(self) -> Any:
        if isinstance(self.name, int):
            if self.name >= len(self.matcher.line) :
                return None
            else:
                return self.matcher.line[self.name]
        else:
            n = self.matcher.header_index(self.name)
            if not n:
                print(f"Header.to_value: no such header {self.name}")
                return None
            print(f"Header: header index: {self.name} = {n}, line: {self.matcher.line}")
            return self.matcher.line[n]

    def matches(self) -> bool:
        return not self.to_value is None


