# pylint: disable=C0114
from typing import Any
from datetime import date, datetime
from .function import Function
from ..productions import ChildrenException


class AboveBelow(Function):
    """this class implements greater-than, less-than"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            thischild = self.children[0].children[0]
            abovethatchild = self.children[0].children[1]
            a = thischild.to_value(skip=skip)
            b = abovethatchild.to_value(skip=skip)
            if a is None and b is not None or b is None and a is not None:
                self.value = False
            else:
                typed = False
                if isinstance(a, int) or isinstance(a, float):
                    self.value = self._try_numbers(a, b)
                    typed = True
                elif (
                    self.value is None
                    and isinstance(a, datetime)
                    or isinstance(a, date)
                ):
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
        return self.value

    def _above(self) -> bool:
        if self.name == "gt" or self.name == "above" or self.name == "after":
            return True
        elif self.name == "lt" or self.name == "below" or self.name == "before":
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

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)
