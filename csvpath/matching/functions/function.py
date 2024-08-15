from typing import Any
from csvpath.matching.productions.matchable import Matchable


class ChildrenException(Exception):
    pass


class Function(Matchable):
    def __init__(self, matcher: Any, name: str, child: Matchable = None) -> None:
        super().__init__(matcher, name=name)
        self.matcher = matcher
        self._function_or_equality = child
        if child:
            self.add_child(child)

    def __str__(self) -> str:
        return f"""{self._simple_class_name()}.{self.name}({self._function_or_equality if self._function_or_equality is not None else ""})"""

    def reset(self) -> None:
        self.value = None
        self.match = None
        super().reset()

    def _noop_match(self) -> bool:
        return self.match if self.match is not None else True

    def _noop_value(self) -> bool:
        return self.value if self.value is not None else self._noop_match()

    def to_value(self, *, skip=[]) -> bool:
        #
        # in most cases, even trivial ones, a function overrides this method.
        #
        if self in skip:
            return True
        if self._function_or_equality:
            if not self._function_or_equality.matches(skip=skip):
                return False
        print(
            "WARNING: Function.to_value defaulting to True. You should probably override this method."
        )
        return True
