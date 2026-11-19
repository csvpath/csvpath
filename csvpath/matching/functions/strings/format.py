from typing import Any
from csvpath.matching.productions import Term, Variable, Header, Reference
from csvpath.matching.functions.function import Function
from ..args import Args
from ..function_focus import ValueProducer


class Format(ValueProducer):
    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                    Uses the Python string formatting mini language.
                """
            ),
        ]
        if self.name == "interpolate":
            s = self.wrap(
                """\
                    Interpolates a complete Pythonic formatting string with one
                    replacement value. Use { and } to demarcate your replacement
                    pattern. For example, to set a variable to a value as a
                    string, use: @a = interpolate(uuid(), "{}")

                    To format a float to two decimal places, put the format
                    inside the braces: interpolate(3.14159, "{:.2f}") gives "3.14".
                """
            )
        else:
            s = self.wrap(
                """\
                    The format argument is a format spec alone, with no braces
                    and no leading colon. For example, to format a float to two
                    decimal places: format(3.14159, ".2f") gives "3.14".

                    A header value is a string. To format it as a number,
                    convert it first: format(float(#price), ".2f").
                """
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
