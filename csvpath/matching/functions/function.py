from typing import Any
from csvpath.matching.productions.matchable import Matchable


class ChildrenException(Exception):
    pass


class Function(Matchable):
    def __init__(self, matcher: Any, name: str, child: Matchable = None) -> None:
        super().__init__(matcher, name=name)
        self.matcher = matcher  # atm, circular dep
        self._function_or_equality = child
        if child:
            self.add_child(child)

    def __str__(self) -> str:
        return f"""\n{self.__class__}{self.name}({self._function_or_equality})"""

    def reset(self) -> None:
        self.value = None
        self.match = None
        super().reset()

    def _noop_match(self) -> bool:
        return self.match if self.match is not None else True

    def _noop_value(self) -> bool:
        return self.value if self.value is not None else self._noop_match()

    def to_value(self, *, skip=[]) -> bool:
        if self in skip:
            return True
        if self._function_or_equality:
            if not self._function_or_equality.matches(skip=skip):
                return False
        print("WARNING: function getting to_value defaulting to True")
        return True  # leave this for now for testing
