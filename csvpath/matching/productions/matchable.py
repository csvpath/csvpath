from enum import Enum
from typing import Any, Self, Optional
from ..expression_utility import ExpressionUtility
from .qualified import Qualified


class Matchable(Qualified):
    def __init__(self, matcher, *, value: Any = None, name: str = None):
        super().__init__(matcher, value=value, name=name)
        self.parent = None
        self.children = []
        self.matcher = matcher
        self.value = value
        self.match = None
        self._id: str = None

    def __str__(self) -> str:
        return f"""{self.__class__}"""

    def line_matches(self):
        es = self.matcher.expressions
        for e in es:
            m = e[0].matches(skip=[self])
            if not m:
                return False
        return True

    def reset(self) -> None:
        # let the subclasses handle value
        # self.value = None
        for child in self.children:
            child.reset()

    def matches(self, *, skip=[]) -> bool:
        return True  # leave this for now for testing

    def to_value(self, *, skip=[]) -> Any:
        return None

    def index_of_child(self, o) -> int:
        return self.children.index(o)

    def set_parent(self, parent: Self) -> None:
        self.parent = parent

    def add_child(self, child: Self) -> None:
        if child:
            child.set_parent(self)
            if child not in self.children:
                self.children.append(child)

    def get_id(self, child: Self = None) -> str:
        if not self._id:
            thing = self if not child else child
            self._id = ExpressionUtility.get_id(thing=thing)
        return self._id
