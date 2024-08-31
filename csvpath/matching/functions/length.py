from typing import Any
from .function import Function
from ..productions import Term, Variable, Header
from csvpath import ConfigurationException


class Length(Function):
    def check_valid(self) -> None:
        self.validate_one_arg(types=[Term, Variable, Header, Function])
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        val = self.children[0].to_value(skip=skip)
        ret = 0
        if val:
            ret = len(f"{val}")
        return ret

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()

        return self.to_value(skip=skip) > 0


class MinMaxLength(Function):
    def check_valid(self) -> None:
        self.validate_two_args(left=[Term, Variable, Header, Function], right=[Term])
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            value = self.children[0].left.to_value()
            length = self.children[0].right.to_value()
            length = int(length)
            if self.name == "min_length" or self.name == "too_long":
                self.value = len(value) >= length
            elif self.name == "max_length" or self.name == "too_short":
                self.value = len(value) <= length
            else:
                raise ConfigurationException("Unknown function name: {self.name}")
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()

        return self.to_value(skip=skip) > 0
