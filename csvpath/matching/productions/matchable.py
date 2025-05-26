# pylint: disable=C0114
import traceback
from typing import Any
from ..util.expression_utility import ExpressionUtility
from .qualified import Qualified
from ..util.exceptions import ChildrenException, MatchException


class Matchable(Qualified):  # pylint: disable=R0904
    """intermediate ancestor of match productions providing
    utility functions and the core to_value and matches
    methods"""

    # re: R0904: too many public methods. we could separate some out but I
    # don't love a deeper class chain or multiple inheritance. igore for now.
    #
    FAILED_VALUE = -99999999
    """ used to signal to Function that a value failed validation. the
        signal allows Function to continue to validate children without
        failing to raise an exception once that happens."""

    def __init__(self, matcher, *, value: Any = None, name: str = None):
        super().__init__(name=name)
        self.parent = None
        self.children = []
        self.matcher = matcher
        self.value = value
        self.match = None
        self._id: str = None

    def _cap_name(self) -> str:
        return f"{self.name[0].upper()}{self.name[1:].replace('_', ' ')}"

    def _a_an(self) -> str:
        return "an" if self.name[0] in ["a", "e", "i", "o", "u"] else "a"

    def __str__(self) -> str:
        return f"""{self._simple_class_name()}"""

    def named_value(self) -> str:
        if self.qualified_name is None:
            return f"""{self._simple_class_name()}({self.value})"""
        return f"""{self._simple_class_name()}({self.qualified_name}:{self.value})"""

    #
    # exp!
    #
    # from csvpath.matching.matcher import What
    def assign(self):
        return self.matcher.what(self, "assign")

    def when_do(self):
        return self.matcher.what(self, "when/do")

    def equality(self):
        return self.matcher.what(self, "equality")

    def matching(self):
        return self.matcher.what(self, "matching")

    def valuing(self):
        return self.matcher.what(self, "value")

    def check_valid(self) -> None:
        """structural check; doesn't test the values. nothing should
        test or use the values until this test is completed."""
        for _ in self.children:
            _.check_valid()

    def clear_caches(self) -> None:
        """most matchables won't cache anything, but references will. we
        don't want that info after a run completes"""

    def _simple_class_name(self) -> str:
        return ExpressionUtility.simple_class_name(self)

    def to_json(self) -> str:
        return self.matcher.to_json(self)

    @property
    def my_chain(self) -> str:
        return ExpressionUtility.my_chain(self)

    def _noop_match(self) -> bool:
        """deprecated. use self.default_match()"""
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

    def set_parent(self, parent) -> None:  # pylint: disable=C0116
        self.parent = parent

    def add_child(self, child) -> None:  # pylint: disable=C0116
        if child:
            child.set_parent(self)
            if child not in self.children:
                self.children.append(child)

    def get_id(self, child=None) -> str:  # pylint: disable=C0116
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

    def _value_three(self, skip=None):
        c = self._child_three()
        if c is None:
            return None
        return c.to_value(skip=skip)

    def _child_three(self):
        if len(self.children) == 0:
            # validation should have already caught this, if it is a problem
            return None
        if len(self.children[0].children) > 2:
            return self.children[0].children[2]
        return None

    def _value_four(self, skip=None):
        c = self._child_four()
        if c is None:
            return None
        return c.to_value(skip=skip)

    def _child_four(self):
        if len(self.children) == 0:
            # validation should have already caught this, if it is a problem
            return None
        if len(self.children[0].children) > 3:
            return self.children[0].children[3]
        return None

    def _value_five(self, skip=None):
        c = self._child_five()
        if c is None:
            return None
        return c.to_value(skip=skip)

    def _child_five(self):
        if len(self.children) == 0:
            # validation should have already caught this, if it is a problem
            return None
        if len(self.children[0].children) > 4:
            return self.children[0].children[4]
        return None

    def siblings_or_equality(self) -> list:
        if (
            len(self.children) == 1
            and hasattr(self.children[0], "op")
            and self.children[0].op == "=="
        ):
            # we're asked for equalities, so we give those that are ==,
            # but not assignments. if we were doing regular siblings we'd
            # give back the children of the equality, not our equality
            # child itself.
            return self.children[:]
        return self.siblings()

    def siblings(self) -> list:
        if len(self.children) == 0:
            return []
        if (
            len(self.children) == 1
            and hasattr(self.children[0], "op")
            and self.children[0].op == ","
        ):
            return self.children[0].commas_to_list()
        #
        #
        #
        if len(self.children) == 1 and hasattr(self.children[0], "op"):
            return self.children[0].children
        #
        #
        #
        if len(self.children) == 1:
            return [self.children[0]]
        if hasattr(self, "op") and self.op == ",":  # pylint: disable=E1101
            # re: E1101: instance has no member: we know, hence the test.
            return self.children
        #
        # this seems likely to be only a dev error, so we'll not check do_i_raise()
        # for now. reassess if it is ever seen.
        #
        raise ChildrenException(
            f"Unexpected number of children, {len(self.children)}, in {self}"
        )

    def sibling_values(self, skip=None):
        sibs = self.siblings()
        vs = []
        for sib in sibs:
            v = sib.to_value(skip=skip)
            vs.append(v)
        return vs

    def default_match(self) -> bool:
        return self.matcher._AND
