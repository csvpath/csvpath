# pylint: disable=C0114
from datetime import date, datetime
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import MatchDecider
from ..args import Args
from ..function import Function
from csvpath.matching.productions import Header, Variable, Reference, Term


class AboveBelow(MatchDecider):
    """this class implements greater-than, less-than"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        #
        # None is an acceptable value >, < None is False
        # we make that comparison frequently. int > date is
        # not Ok. we never expect that comparison.
        #
        a.arg(
            types=[Term, Variable, Header, Function, Reference],
            actuals=[None, int, date, datetime, str],
        )
        a.arg(
            types=[Term, Variable, Header, Function, Reference],
            actuals=[None, int, date, datetime, str],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        thischild = self.children[0].children[0]
        abovethatchild = self.children[0].children[1]
        a = thischild.to_value(skip=skip)
        b = abovethatchild.to_value(skip=skip)
        if a is None and b is not None or b is None and a is not None:
            self.match = False
        else:
            if ExpressionUtility.all([a, b], [float, int]):
                self.match = self._try_numbers(a, b)
            elif ExpressionUtility.all([a, b], [datetime]):
                self.match = self._try_dates(a, b)
            elif ExpressionUtility.all([a, b], [date]):
                self.match = self._try_dates(a, b)
            else:
                self.match = self._try_strings(a, b)
        if self.match is None:
            self.match = False  # pragma: no cover

    def _above(self) -> bool:
        if self.name in ["gt", "above", "after", "gte"]:
            return True
        if self.name in ["lt", "below", "before", "lte"]:
            return False

    def _try_numbers(self, a, b) -> bool:
        if self._above() and self.name != "gte":
            return float(a) > float(b)
        elif self._above():
            return float(a) >= float(b)
        if not self._above() and self.name != "lte":
            float(a) < float(b)
        return float(a) <= float(b)

    def _try_dates(self, a, b) -> bool:
        if ExpressionUtility.all([a, b], [datetime]):
            if self._above() and self.name != "gte":
                return a.timestamp() > b.timestamp()
            elif self._above():
                return a.timestamp() >= b.timestamp()
            if not self._above() and self.name != "lte":
                a.timestamp() < b.timestamp()
            return a.timestamp() <= b.timestamp()
        if ExpressionUtility.all([a, b], [date]):
            if self._above() and self.name != "gte":
                return a > b
            elif self._above():
                return a >= b
            if not self._above() and self.name != "lte":
                a < b
            return a <= b
        return None

    def _try_strings(self, a, b) -> bool:
        a = f"{a}".strip()
        b = f"{b}".strip()
        if self._above() and self.name != "gte":
            return a > b
        elif self._above():
            return a >= b
        if not self._above() and self.name != "lte":
            a < b
        return a <= b
