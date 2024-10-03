# pylint: disable=C0114
from typing import Any
from ..function_focus import SideEffect
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args


class Track(SideEffect):
    """uses a match component value to set a tracking
    value, from another match component, on a variable."""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[str])
        # typically arg two is going to be a string, but it can be anything. there
        # have definitely been cases of int and bool
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[Any])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        left = self.children[0].children[0]
        right = self.children[0].children[1]
        varname = self.first_non_term_qualifier(self.name)
        tracking = f"{left.to_value(skip=skip)}".strip()
        v = right.to_value(skip=skip)
        if isinstance(v, str):
            v = f"{v}".strip()
        value = v
        self.matcher.set_variable(varname, tracking=tracking, value=value)
        self.match = self.default_match()
