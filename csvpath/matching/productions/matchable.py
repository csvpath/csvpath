# pylint: disable=C0114
from typing import Any, Self
from ..util.expression_utility import ExpressionUtility
from .qualified import Qualified


class Matchable(Qualified):
    """intermediate ancestor of match productions providing
    utility functions and the core to_value and matches
    methods"""

    def __init__(self, matcher, *, value: Any = None, name: str = None):
        super().__init__(name=name)
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
            if not m:
                return False
        return True

    def reset(self) -> None:
        # let the subclasses handle self.value and self.match
        for child in self.children:
            child.reset()

    def matches(self, *, skip=None) -> bool:  # pylint: disable=W0613
        #
        # subclasses should override this method for clarity
        # we can ignore W0613. this method essentially defines an interface.
        #
        return True

    def to_value(self, *, skip=None) -> Any:  # pylint: disable=W0613
        #
        # subclasses should override this method for clarity.
        # we can ignore W0613. this method essentially defines an interface.
        #
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
    def _value_one(self, skip=None):
        if len(self.children) == 0:
            # validation should have already caught this, if it is a problem
            return None
        elif hasattr(self.children[0], "left"):
            return self.children[0].left.to_value(skip=skip)
        else:
            return self.children[0].to_value(skip=skip)

    # convenience method for one or two arg functions
    def _value_two(self, skip=None):
        if len(self.children) == 0:
            # validation should have already caught this, if it is a problem
            return None
        if hasattr(self.children[0], "right"):
            return self.children[0].right.to_value(skip=skip)
        # with the current parse tree this shouldn't happen
        return None
