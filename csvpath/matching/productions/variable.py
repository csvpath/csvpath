from typing import Any
from csvpath.matching.productions.matchable import Matchable


class Variable(Matchable):
    def __init__(self, matcher, *, value: Any = None, name: str = None):
        super().__init__(matcher, value=value, name=name)
        #
        # onmatch is a qualifier, but it was created first, so is more specific.
        #
        self.onmatch = False
        dot = name.find(".")
        if dot > -1:
            self.name = name[0:dot]
            om = name[dot + 1 :]
            om = om.strip()
            if om == "onmatch":
                self.onmatch = True

    def __str__(self) -> str:
        return f"""{self.__class__}: {self.name}"""

    def reset(self) -> None:
        self.value = None
        super().reset()

    def matches(self, *, skip=[]) -> bool:
        return self.value is not None

    def to_value(self, *, skip=[]) -> Any:
        if not self.value:
            self.value = self.matcher.get_variable(self.name)
        return self.value
