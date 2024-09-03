# pylint: disable=C0114
from typing import Any
from .function import Function


class Mismatch(Function):
    """tests the current headers against an expectation"""

    def check_valid(self) -> None:
        self.validate_zero_or_one_arg()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            if not self.onmatch or self.line_matches():
                hs = len(self.matcher.csvpath.headers)
                ls = len(self.matcher.line)
                if ls == 1 and f"{self.matcher.line[0]}".strip() == "":
                    # blank line with some whitespace chars. we don't take credit for those characters.
                    self.value = hs
                else:
                    ab = True
                    if len(self.children) == 1:
                        v = self.children[0].to_value()
                        if isinstance(v, str):
                            av = v.strip().lower()
                            if av == "true":
                                ab = True
                            elif av == "false" or av == "signed":
                                ab = False
                        else:
                            ab = bool(v)
                    if ab:
                        self.value = abs(hs - ls)
                    else:
                        signed = ls - hs
                        self.value = signed
            else:
                self.value = 0
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            self.match = self.to_value(skip=skip) != 0
        return self.match
