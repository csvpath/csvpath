from typing import Any
from .function import Function
from ..productions import ChildrenException
from datetime import date, datetime


class AboveBelow(Function):
    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            thischild = self.children[0].children[0]
            abovethatchild = self.children[0].children[1]
            a = thischild.to_value(skip=skip)
            b = abovethatchild.to_value(skip=skip)
            if a is None and b is not None or b is None and a is not None:
                self.value = False
            else:
                print(f"AboveBelow.to_value: a: {a}, b: {b}")
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
        else:
            raise ChildrenException(f"{self.name}() is not a known function")

    def _try_numbers(self, a, b) -> bool:
        try:
            if self._above():
                return float(a) > float(b)
            else:
                return float(a) < float(b)
        except Exception:
            return None

    def _try_dates(self, a, b) -> bool:
        if isinstance(a, datetime):
            try:
                print("AboveBelow.try_dates: a, b")
                if self._above():
                    return a.timestamp() > b.timestamp()
                else:
                    return a.timestamp() < b.timestamp()
            except Exception as ex:
                print(f"AboveBelow.try_dates: datetime exception: ex: {ex}")
                return None
        else:
            try:
                print("AboveBelow.try_dates: a, b")
                if self._above():
                    return a > b
                else:
                    return a < b
            except Exception as ex:
                print(f"AboveBelow.try_dates: date exception: ex: {ex}")
                return None

    def _try_strings(self, a, b) -> bool:
        if isinstance(a, str) and isinstance(b, str):
            if self._above():
                return a.strip() > b.strip()
            else:
                return a.strip() < b.strip()
        else:
            if self._above():
                return f"{a}".strip() > f"{b}".strip()
            else:
                return f"{a}".strip() < f"{b}".strip()

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)
