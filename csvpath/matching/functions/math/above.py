# pylint: disable=C0114
from datetime import date, datetime
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import MatchDecider


class AboveBelow(MatchDecider):
    """this class implements greater-than, less-than"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip)

    def _produce_value(self, skip=None) -> None:
        thischild = self.children[0].children[0]
        abovethatchild = self.children[0].children[1]
        a = thischild.to_value(skip=skip)
        b = abovethatchild.to_value(skip=skip)
        if a is None and b is not None or b is None and a is not None:
            self.value = False
        else:
            typed = False
            if isinstance(a, (float, int)):  # or isinstance(a, float):
                self.value = self._try_numbers(a, b)
                typed = True
            elif self.value is None and isinstance(
                a, (datetime, date)
            ):  # or isinstance(a, date):
                self.value = self._try_dates(a, b)
                typed = True
            if typed:
                # we're done
                pass
            else:
                if self.value is None:
                    self.value = self._try_strings(a, b)
        if self.value is None:
            self.value = False

    def _above(self) -> bool:
        if self.name in ["gt", "above", "after"]:
            return True
        if self.name in ["lt", "below", "before"]:
            return False
        raise ChildrenException(f"{self.name}() is not a known function")

    def _try_numbers(self, a, b) -> bool:
        try:
            if self._above():
                return float(a) > float(b)
            return float(a) < float(b)
        except (ValueError, TypeError):
            return None

    def _try_dates(self, a, b) -> bool:
        if isinstance(a, datetime):
            try:
                if self._above():
                    return a.timestamp() > b.timestamp()
                return a.timestamp() < b.timestamp()
            except (TypeError, AttributeError):
                return None
        else:
            try:
                if self._above():
                    return a > b
                return a < b
            except TypeError:
                return None

    def _try_strings(self, a, b) -> bool:
        if isinstance(a, str) and isinstance(b, str):
            if self._above():
                return a.strip() > b.strip()
            return a.strip() < b.strip()
        if self._above():
            return f"{a}".strip() > f"{b}".strip()
        return f"{a}".strip() < f"{b}".strip()
