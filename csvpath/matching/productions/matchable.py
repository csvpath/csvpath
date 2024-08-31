from enum import Enum
from typing import Any, Self, Optional
from ..util.expression_utility import ExpressionUtility
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

    def check_valid(self) -> None:
        for _ in self.children:
            _.check_valid()

    def _simple_class_name(self) -> str:
        cn = str(self.__class__)
        name = cn[(cn.rfind(".") + 1) :]
        name = name[0 : name.rfind("'>")]
        return name

    def line_matches(self):
        es = self.matcher.expressions
        for e in es:
            m = e[1] is True or e[0].matches(skip=[self])
            # m = e[0].matches(skip=[self])
            if not m:
                return False
        return True

    def has_not_yet(self):
        id = self.get_id()
        v = self.matcher.get_variable(id, set_if_none=True)
        return v

    def set_has_happened(self) -> None:
        id = self.get_id()
        self.matcher.set_variable(id, value=False)

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
        self.matcher.csvpath.logger.debug(
            f"Matchable.get_id: for child: {child} or self: {self}"
        )
        if not self._id:
            thing = self if not child else child
            self._id = ExpressionUtility.get_id(thing=thing)
        return self._id

    # convenience method for one or two arg functions
    def _value_one(self):
        if len(self.children) == 0:
            # validation should have already caught this, if it is a problem
            return None
        elif hasattr(self.children[0], "left"):
            return self.children[0].left.to_value()
        else:
            return self.children[0].to_value()

    # convenience method for one or two arg functions
    def _value_two(self):
        if len(self.children) == 0:
            # validation should have already caught this, if it is a problem
            return None
        if hasattr(self.children[0], "right"):
            return self.children[0].right.to_value()
        else:
            # with the current parse tree this shouldn't happen
            return None
