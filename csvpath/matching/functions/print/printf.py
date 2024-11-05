# pylint: disable=C0114
from typing import Any
from csvpath.matching.productions import Equality, Term
from csvpath.matching.util.print_parser import PrintParser
from ..function_focus import SideEffect
from ..function import Function
from ..args import Args


class Print(SideEffect):
    """the print function handles parsing print lines, interpolating
    values, and sending to the Printer instances. a 2nd argument is:
        - if a Term, an indicator of a print stream/target/file
        - if a function or equality, a matches() to call after the print"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(name="print this", types=[Term], actuals=[str, self.args.EMPTY_STRING])
        a.arg(
            name="print to specific printer",
            types=[None, Term],
            actuals=[str, self.args.EMPTY_STRING],
        )
        a = self.args.argset(2)
        a.arg(name="print this", types=[Term], actuals=[str, self.args.EMPTY_STRING])
        a.arg(
            name="run matches",
            types=[None, Function, Equality],
            actuals=[Any],
        )
        self.args.validate(self.siblings_or_equality())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        right = self._child_two()
        if self.do_onchange():
            if self.do_once():
                child = None
                if isinstance(self.children[0], Equality):
                    child = self.children[0].left
                else:
                    child = self.children[0]
                string = child.to_value()
                parser = PrintParser(csvpath=self.matcher.csvpath)
                v = parser.transform(string)
                #
                # we intentionally add a single char suffix
                #
                if v[len(v) - 1] == " ":
                    v = v[0 : len(v) - 1]
                file = right.to_value() if right and isinstance(right, Term) else None
                if file is not None:
                    self.matcher.csvpath.print_to(file, f"{v}")
                else:
                    self.matcher.csvpath.print(f"{v}")
                    if right is not None:
                        right.matches(skip=skip)
                self._set_has_happened()
        self.match = self.default_match()
