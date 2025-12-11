# pylint: disable=C0114
from typing import Any
from ..function_focus import SideEffect
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args


class Put(SideEffect):
    """Sets a variable with or without a tracking value"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Sets a variable that tracks keyed-values.

                    A tracking value is similar to a dictionary key. It usually keys a
                    count, calculation, or transformation.

                    Calling put() with one argument, a var name, creates an empty dictionary.

                    Calling put() with two arguments creates a regular named-value variable.

                    Calling put() with three arguments creates a dictionary, if needed, and
                    uses the second variable as the key to store and access the third.

                    While get() and put() make it possible to create and use tracking-value
                    variables in an ad hoc dict-like way, this is not recommended unless there
                    is no simplier solution based on more specific functions.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="new var name",
            types=[Term],
            actuals=[str],
        )
        a = self.args.argset(2)
        a.arg(
            name="var name",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str],
        )
        a.arg(
            name="var value",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[Any],
        )
        a = self.args.argset(3)
        a.arg(
            name="var name",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str],
        )
        a.arg(
            name="tracking key",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str],
        )
        a.arg(
            name="tracking value",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[Any],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        sibs = self.siblings()
        varname = None
        varname = sibs[0].to_value(skip=skip)
        if len(sibs) == 1:
            self.matcher.set_variable(varname, value={})
        else:
            key = sibs[1].to_value(skip=skip)
            value = None
            if len(sibs) > 2:
                value = sibs[2].to_value(skip=skip)
            else:
                value = key
                key = None
            self.matcher.set_variable(varname, value=value, tracking=key)
        self.value = self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip) is not None  # pragma: no cover
