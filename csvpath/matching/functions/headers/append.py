# pylint: disable=C0114
import datetime
from typing import Any
from ..function_focus import SideEffect
from csvpath.matching.productions import Term, Header, Reference, Variable
from ..function import Function
from ..args import Args


class Append(SideEffect):
    """appends the header and value to the lines of the file being iterated"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(types=[Term], actuals=[str])
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[None, Any])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        header = self._value_one(skip=skip)
        val = self._value_two(skip=skip)
        self.matcher.line.append(val)
        h = self.matcher.csvpath.headers
        if not h[len(h) - 1] == header:
            h.append(header)
        self.match = self.default_match()
