# pylint: disable=C0114

from datetime import datetime
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import MatchDecider


class Between(MatchDecider):
    """this class implements a date, number or string between test"""

    def check_valid(self) -> None:
        self.validate_three_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        siblings = self.children[0].commas_to_list()
        me = siblings[0].to_value(skip=skip)
        a = siblings[1].to_value(skip=skip)
        b = siblings[2].to_value(skip=skip)
        if me is None or a is None or b is None:
            self.match = False
        else:
            self.match = self._try_numbers(me, a, b)
            if self.match is None:
                self.match = self._try_dates(me, a, b)
            if self.match is None:
                self.match = self._try_strings(me, a, b)
        if self.match is None:
            self.match = False

    # =====================

    def _between(self) -> bool:
        if self.name in ["between", "inside"]:
            return True
        if self.name in ["beyond", "outside"]:
            return False
        raise ChildrenException(f"{self.name}() is not a known function")

    def _try_numbers(self, me, a, b) -> bool:
        try:
            return self._order(float(me), float(a), float(b))
        except (ValueError, TypeError):
            return None

    def _try_dates(self, me, a, b) -> bool:
        if isinstance(a, datetime):
            try:
                return self._order(me.timestamp(), a.timestamp(), b.timestamp())
            except (TypeError, AttributeError):
                return None
        else:
            ret = None
            try:
                return self._order(me, a, b)
            except TypeError:
                ret = None
            return ret

    def _try_strings(self, me, a, b) -> bool:
        if isinstance(a, str) and isinstance(b, str):
            return self._order(f"{me}".strip(), a.strip(), b.strip())
        return self._order(f"{me}".strip(), f"{a}".strip(), f"{b}".strip())

    def _order(self, me, a, b):
        if a > b:
            return self._compare(a, me, b)
        return self._compare(b, me, a)

    def _compare(self, high, med, low):
        between = self._between()
        if between:
            return high > med > low
        return (high < med and low < med) or (high > med and low > med)
