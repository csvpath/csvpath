# pylint: disable=C0114
from typing import Any as AnyType

from .headers import Headers
from .variables import Variables
from .function import Function
from ..productions import Equality, Term, ChildrenException


class Any(Function):
    """this class checks various places to find any values present.
    - any()
    - any(header())
    - any(variable())
    - any(term)
    - any(header(), term)
    - any(variable(), term)
    """

    def check_valid(self) -> None:
        self.validate_zero_one_or_two_args(
            first_arg=[Variables, Headers],
            solo_arg=[Term, Headers, Variables],
            second_arg=[Term],
        )
        super().check_valid()

    def to_value(self, *, skip=None) -> AnyType:
        return self.matches(skip=skip)  # pragma: no cover

    def matches(self, *, skip=None) -> bool:
        # re: R0912: complexity is too high. _bare_any() should help. plan to refactor.
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            self.match = False
            if not self.onmatch or self.line_matches():
                if len(self.children) == 1:
                    if isinstance(self.children[0], Equality):
                        self.equality()
                    elif isinstance(self.children[0], Variables):
                        # any(variable())
                        self.variable()
                    elif isinstance(self.children[0], Headers):
                        # any(header())
                        self.header()
                    else:
                        # any(Term) we check in both headers and vars for any matches
                        self.check_value()
                else:
                    # any()
                    self._bare_any()
        return self.match

    def _bare_any(self) -> None:
        for h in self.matcher.line:
            if h is None:
                continue
            if f"{h}".strip() == "":
                continue
            self.match = True
            break
        if self.match is False:
            for v in self.matcher.csvpath.variables.values():
                if v is None:
                    continue
                if f"{v}".strip() == "":
                    continue
                self.match = True
                break

    def check_value(self):  # pylint: disable=C0116
        value = self.children[0].to_value()
        for h in self.matcher.line:
            if f"{h}" == f"{value}":
                self.match = True
                break
            if self.match is False:
                for v in self.matcher.csvpath.variables.values():
                    if f"{v}" == f"{value}":
                        self.match = True
                        break

    def header(self):  # pylint: disable=C0116
        for h in self.matcher.line:
            if h is None:
                continue
            if f"{h}".strip() == "":
                continue
            self.match = True
            break

    def variable(self):  # pylint: disable=C0116
        for v in self.matcher.csvpath.variables.values():
            if v is None:
                continue
            if f"{v}".strip() == "":
                continue
            self.match = True
            break

    def equality(self):  # pylint: disable=C0116
        value = self.children[0].right.to_value()
        if isinstance(self.children[0].left, Headers):
            for h in self.matcher.line:
                if f"{h}" == f"{value}":
                    self.match = True
                    break
        elif isinstance(self.children[0].left, Variables):
            for v in self.matcher.csvpath.variables.values():
                if f"{v}" == f"{value}":
                    self.match = True
                    break
        else:
            c = self.children[0].left
            raise ChildrenException(
                f"Left child of any() must be header or variable, not {c}"
            )
