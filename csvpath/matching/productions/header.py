from typing import Any
from csvpath.matching.productions.matchable import Matchable


class Header(Matchable):
    NEVER = -9999999999

    def __str__(self) -> str:
        return f"""{self.__class__}: {self.name} """

    def __init__(self, matcher, *, value: Any = None, name: str = None) -> None:
        super().__init__(matcher, value=Header.NEVER, name=name)

    def reset(self) -> None:
        self.value = Header.NEVER
        super().reset()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return self.value
        if self.value == Header.NEVER:
            ret = Header.NEVER
            if isinstance(self.name, int):
                if self.name >= len(self.matcher.line):
                    ret = None
                else:
                    ret = self.matcher.line[self.name]
            else:
                n = self.matcher.header_index(self.name)
                if n is None:
                    ret = None
                if self.matcher.line and len(self.matcher.line) > n:
                    ret = self.matcher.line[n]
            self.value = ret
        return self.value

    def matches(self, *, skip=[]) -> bool:
        v = self.to_value(skip=skip)
        return v is not None
