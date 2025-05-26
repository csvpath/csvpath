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
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
            Adds the header name and a value to the end of every line.
            The name is added to the headers and available for use in the csvpath.
            An appended header becomes part of the headers when it is first set. If
            The append() is conditional to a when/do operator there could be lines
            that do not have the appended header; however, after the first appended
            line all lines have the appended header.
            """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(3)
        a.arg(name="name of appended header", types=[Term], actuals=[str])
        a.arg(
            name="value",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[None, Any],
        )
        a.arg(
            name="append header name to header row data",
            types=[None, Term, Function],
            actuals=[bool],
        )
        self.args.validate(self.siblings())
        super().check_valid()
        #
        # found is a check if we have already appended a header. if True
        # we can avoid iterating to see if the header exists.
        #
        self.found = False

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        new_header = self._value_one(skip=skip)
        val = self._value_two(skip=skip)
        first_to_data = self._value_three(skip=skip)

        headers = self.matcher.csvpath.headers
        first = False
        if self.found is False:
            for header in headers:
                if header == new_header:
                    self.found = True
                    break
            if self.found is False:
                headers.append(new_header)
                self.found = True
                if first_to_data is True:
                    self.matcher.line.append(new_header)
                    first = True

        if first is False:
            self.matcher.line.append(val)

        self.match = self.default_match()
