# pylint: disable=C0114
from csvpath.matching.productions import Equality, Term
from csvpath.matching.util.print_parser import PrintParser
from ..function_focus import SideEffect
from ..function import Function


class Print(SideEffect):
    """the print function handles parsing print lines, interpolating
    values, and sending to the Printer instances"""

    def check_valid(self) -> None:
        self.validate_one_or_two_args(
            one=[Term], left=[Term], right=[Function, Equality]
        )
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = None
        if isinstance(self.children[0], Equality):
            child = self.children[0].left
        else:
            child = self.children[0]
        string = child.to_value()
        parser = PrintParser(self.matcher.csvpath)
        self.value = parser.transform(string)

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            right = None
            if isinstance(self.children[0], Equality):
                right = self.children[0].right
            if self.do_onmatch():
                if self.do_onchange():
                    self.matcher.csvpath.print(f"{self.to_value()}")
                    if right:
                        right.matches(skip=skip)
            self.match = True
        return self.match
