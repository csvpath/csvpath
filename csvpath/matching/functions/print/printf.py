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
        parser = PrintParser(csvpath=self.matcher.csvpath)
        self.value = parser.transform(string)

    def _decide_match(self, skip=None) -> None:
        right = None
        if isinstance(self.children[0], Equality):
            right = self.children[0].right
        if self.do_onchange():
            if self.do_once():
                v = self.to_value(skip=skip)
                #
                # we intentionally add a single char suffix
                #
                if v[len(v) - 1] == " ":
                    v = v[0 : len(v) - 1]
                self.matcher.csvpath.print(f"{v}")
                if right:
                    right.matches(skip=skip)
                self._set_has_happened()

        self.match = True
