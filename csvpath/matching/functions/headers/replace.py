# pylint: disable=C0114
from typing import Any
from ..function_focus import SideEffect
from csvpath.matching.productions import Term, Header, Reference, Variable
from ..function import Function
from ..args import Args


class Replace(SideEffect):
    """replaces the value of the header with another value"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(types=[Term, Header], actuals=[int, str])
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[Any])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        header = None
        c = self._child_one()
        if isinstance(c, Header):
            header = c.name
        else:
            header = self._value_one(skip=skip)
        i = header
        if not isinstance(header, int):
            i = self.matcher.header_index(header)

        val = self._value_two(skip=skip)

        self.matcher.csvpath.logger.debug(
            "Replacing %s idenified as %s with %s", self.matcher.line[i], header, val
        )
        self.matcher.line[i] = val

        self.match = self.default_match()
