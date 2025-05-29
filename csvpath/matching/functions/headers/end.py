# pylint: disable=C0114
from typing import Any
from csvpath.matching.productions import Term
from csvpath.matching.util.exceptions import DataException
from ..function_focus import ValueProducer
from ..args import Args


class End(ValueProducer):
    """returns the value of the last header"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
            Returns the value of the last header.

            If an integer argument N is given, the return is the value of the
            last header minus N.

            I.e., if the last header is #11, end(3) returns the value of header #8.
            """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.argset(1).arg(
            name="positions to the left of end", types=[None, Any], actuals=[int]
        )
        self.args.validate(self.siblings())

        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        i = self.matcher.last_header_index()
        if i is None:
            # this could happen when a line is blank or has some other oddity
            pass
        else:
            if len(self.children) > 0:
                v = self.children[0].to_value()
                i = i - abs(int(v))
            if 0 <= i < len(self.matcher.line):
                self.value = self.matcher.line[i]

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip) is not None
