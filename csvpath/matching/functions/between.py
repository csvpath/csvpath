# pylint: disable=C0114

from typing import Any
from .function import Function
from ..productions import ChildrenException
from datetime import date, datetime


class Between(Function):
    def check_valid(self) -> None:
        self.validate_three_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            siblings = self.children[0].commas_to_list()
            me = siblings[0].to_value(skip=skip)
            a = siblings[1].to_value(skip=skip)
            b = siblings[2].to_value(skip=skip)
            if me is None or a is None or b is None:
                self.value = False
            else:
                # simple approach for now.
                self.value = self._try_numbers(me, a, b)
                if self.value is None:
                    self.value = self._try_dates(me, a, b)
                if self.value is None:
                    self.value = self._try_strings(me, a, b)
            if self.value is None:
                self.value = False
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)

    # =====================

    def _between(self) -> bool:
        if self.name == "between" or self.name == "inside":
            return True
        elif self.name == "beyond" or self.name == "outside":
            return False
        else:
            raise ChildrenException(f"{self.name}() is not a known function")

    def _try_numbers(self, me, a, b) -> bool:
        try:
            return self._order(float(me), float(a), float(b))
        except Exception:
            return None

    def _try_dates(self, me, a, b) -> bool:
        if isinstance(a, datetime):
            try:
                return self._order(me.timestamp(), a.timestamp(), b.timestamp())
            except Exception:
                return None
        else:
            ret = None
            try:
                return self._order(me, a, b)
            except Exception:
                ret = None
            return ret

    def _try_strings(self, me, a, b) -> bool:
        try:
            if isinstance(a, str) and isinstance(b, str):
                return self._order(me.strip(), a.strip(), b.strip())
            else:
                return self._order(f"{me}".strip(), f"{a}".strip(), f"{b}".strip())
        except Exception:
            return None

    def _order(self, me, a, b):
        if a > b:
            return self._compare(a, me, b)
        else:
            return self._compare(b, me, a)

    def _compare(self, high, med, low):
        between = self._between()
        if between:
            return high > med and med > low
        else:
            return (high < med and low < med) or (high > med and low > med)
