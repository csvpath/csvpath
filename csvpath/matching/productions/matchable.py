from typing import Any, Self
from csvpath.matching.expression_utility import ExpressionUtility


class Matchable:
    def __init__(self, matcher, *, value: Any = None, name: str = None):
        self.parent = None
        self.children = []
        self.matcher = matcher
        self.value = value
        self.name = name
        self._id: str = None
        if self.name and self.name.__class__ == str:
            self.name = self.name.strip()
        self.qualifier = None
        # self.flag = matcher.next_flag()

    def __str__(self) -> str:
        return f"""{self.__class__}"""

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
