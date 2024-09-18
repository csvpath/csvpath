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
        return f"""{self._simple_class_name()}"""

    def check_valid(self) -> None:
        """structural check; doesn't test the values. nothing should
        test or use the values until this test is completed."""
        for _ in self.children:
            _.check_valid()

    def clear_caches(self) -> None:
        """most matchables won't cache anything, but references will. we
        don't want that info after a run completes"""

    def _simple_class_name(self) -> str:
        cn = str(self.__class__)
        name = cn[(cn.rfind(".") + 1) :]
        name = name[0 : name.rfind("'>")]
        return name

    def _noop_match(self) -> bool:
        return self.match if self.match is not None else True

    def _noop_value(self) -> bool:
        return self.value if self.value is not None else self._noop_match()

    def reset(self) -> None:
        """called after every line to make the match components ready
        for the next line"""
        # let the subclasses handle self.value and self.match
        for child in self.children:
            child.reset()

    def matches(self, *, skip=None) -> bool:  # pylint: disable=W0613
        """
        subclasses should override this method for clarity even if
        not doing any processing.
        """
        #
        # we can ignore W0613. this method essentially defines an interface.
        #
        return True

    def to_value(self, *, skip=None) -> Any:  # pylint: disable=W0613
        """
        subclasses should prefer to override _produce_value(), but they may
        override this method if there are special requirements.
        """
        #
        # we can ignore W0613. this method essentially defines an interface.
        #
        return None

    def index_of_child(self, o) -> int:  # pylint: disable=C0116
        return self.children.index(o)

    def set_parent(self, parent: Self) -> None:  # pylint: disable=C0116
        self.parent = parent

    def add_child(self, child: Self) -> None:  # pylint: disable=C0116
        if child:
            child.set_parent(self)
            if child not in self.children:
                self.children.append(child)

    def get_id(self, child: Self = None) -> str:  # pylint: disable=C0116
        self.matcher.csvpath.logger.debug(
            f"Matchable.get_id: for child: {child} or self: {self}"
        )
        if not self._id:
            thing = self if not child else child
            self._id = ExpressionUtility.get_id(thing=thing)
        return self._id

    # convenience method for one or two arg functions
    def _value_one(self, skip=None):
        c = self._child_one()
        if c is None:
            return None
        return c.to_value(skip=skip)

    def _child_one(self):
        if len(self.children) == 0:
            # validation should have already caught this, if it is a problem
            return None
        if hasattr(self.children[0], "left"):
            return self.children[0].left
        return self.children[0]

    def _value_two(self, skip=None):
        c = self._child_two()
        if c is None:
            return None
        return c.to_value(skip=skip)

    # convenience method for one or two arg functions
    def _child_two(self):
        if len(self.children) == 0:
            # validation should have already caught this, if it is a problem
            return None
        if hasattr(self.children[0], "right"):
            return self.children[0].right
        # with the current parse tree this shouldn't happen
        return None

    def default_match(self) -> bool:
        return self.matcher._AND
