# pylint: disable=C0114
from typing import Any
from csvpath.matching.util.exceptions import MatchComponentException
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function_focus import ValueProducer
from ..function import Function


class Length(ValueProducer):
    """returns the length of a string"""

    def check_valid(self) -> None:
        self.validate_one_arg(types=[Term, Variable, Header, Function, Reference])
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        val = self.children[0].to_value(skip=skip)
        ret = 0
        if val:
            ret = len(f"{val}")
        self.value = ret

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip) > 0


class MinMaxLength(ValueProducer):  # pylint: disable=C0115
    def check_valid(self) -> None:
        self.validate_two_args(
            left=[Term, Variable, Header, Function, Reference], right=[Term]
        )
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            value = self.children[0].left.to_value()
            length = self.children[0].right.to_value()
            length = int(length)
            if self.name in ["min_length", "too_long"]:
                self.value = len(value) >= length
            elif self.name in ["max_length", "too_short"]:
                self.value = len(value) <= length
        return self.value

    def _decide_match(self, skip=None) -> None:
        v = self.to_value(skip=skip)
        self.match = v
