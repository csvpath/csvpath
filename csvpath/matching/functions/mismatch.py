from typing import Any
from .function import Function


class Mismatch(Function):
    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            hs = len(self.matcher.csvpath.headers)
            ls = len(self.matcher.line)
            self.value = abs(hs - ls)
            print(f"Mismatch.to_value: hs: {hs} - ls: {ls} = self.value: {self.value}")
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            self.match = self.to_value(skip=skip) != 0
        return self.match
