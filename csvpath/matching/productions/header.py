from typing import Any
from csvpath.matching.productions.expression import Matchable

class Header(Matchable):


    def __str__(self) -> str:
        return f"""{self.__class__}: {self.name} """

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if isinstance(self.name, int):
            if self.name >= len(self.matcher.line) :
                return None
            else:
                return self.matcher.line[self.name]
        else:
            n = self.matcher.header_index(self.name)
            #print(f"Header.to_value: n: {n}, a {n.__class__}")
            if n is None:
                #print(f"Header.to_value: no such header {self.name}")
                return None
            #print(f"Header: header index: {self.name} = {n}, line: {self.matcher.line}")
            ret = None
            if self.matcher.line and len(self.matcher.line) > n:
                ret = self.matcher.line[n]
            return ret

    def matches(self, *, skip=[]) -> bool:
        return not self.to_value(skip=skip) is None


