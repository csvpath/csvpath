# pylint: disable=C0114
from typing import Any
from csvpath.matching.productions import Term
from csvpath.matching.util.exceptions import DataException
from ..function_focus import ValueProducer
from ..args import Args


class End(ValueProducer):
    """returns the value of the last header"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.argset(1).arg(types=[None, Any], actuals=[int])
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
