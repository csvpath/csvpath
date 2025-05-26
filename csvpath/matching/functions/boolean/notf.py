# pylint: disable=C0114
from typing import Any
from ..function_focus import MatchDecider
from csvpath.matching.productions import Variable, Header, Reference, Equality
from ..function import Function
from ..args import Args


class Not(MatchDecider):
    """returns the boolean inverse of a value"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    not() returns the boolean inverse of its argument.

                    Optionally, if an function is provided as a second argument, not()
                    will evaluate it as a side-effect if not() evaluates to True.
            """
            ),
        ]

        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="value applied to",
            types=[Variable, Header, Function, Reference, Equality],
            actuals=[None, Any],
        )
        a.arg(
            name="A function to invoke if not() is True",
            types=[None, Function],
            actuals=[None, Any],
        )
        self.args.validate(self.siblings_or_equality())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        c = None
        eq = isinstance(self.children[0], Equality) and self.children[0].op == "=="
        if eq:
            c = self.children[0]
        else:
            c = self._child_one()

        t = self._child_two()
        m = c.matches(skip=skip)

        m = not m
        if m is True:
            if eq is False:
                t = self._child_two()
                if t is not None:
                    t.matches(skip=skip)
        self.match = m
