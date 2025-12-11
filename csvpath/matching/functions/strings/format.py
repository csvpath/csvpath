from typing import Any
from csvpath.matching.productions import Term, Variable, Header, Reference
from csvpath.matching.functions.function import Function
from csvpath.matching.util.exceptions import ChildrenException, MatchException
from ..args import Args
from ..function_focus import ValueProducer


class Format(ValueProducer):
    def check_valid(self) -> None:
        s = ""
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Uses the Python string formatting mini language.

                    E.g. to format a float to having two decimal places use a format argument of “:.2f”
                """
            ),
        ]
        if self.name == "interpolate":
            s = self.wrap(
                """Interpolates a complete Pythonic formatting string with one replacement value.
                Use {{ and }} to demarcate your replacement pattern."""
            )
            self.description.append(s)

        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="value",
            types=[Term, Function, Header, Variable, Reference],
            actuals=[None, Any],
        )
        a.arg(
            name="format",
            types=[Term, Function, Header, Variable, Reference],
            actuals=[str],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        value = self._value_one(skip=skip)
        if value is None:
            return
        format_spec = self._value_two(skip=skip)
        if format_spec is None:
            return
        if self.name == "format":
            self.value = f"{value:{format_spec}}"
        else:
            self.value = format_spec.format(value)

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover
