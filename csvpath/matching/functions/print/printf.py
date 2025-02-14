# pylint: disable=C0114
from typing import Any
from csvpath.matching.productions import Equality, Term
from csvpath.matching.util.print_parser import PrintParser
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import SideEffect
from ..function import Function
from ..args import Args


class Print(SideEffect):
    """the print function handles parsing print lines, interpolating
    values, and sending to the Printer instances. a 2nd argument is:
        - if a Term, an indicator of a print stream/target/file
        - if a function or equality, a matches() to call after the print"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            f"{self.name}() prints to one or more default or designated Printer instances.",
            "Print can have a function or equality argument that is evaluated after printing completes.",
        ]
        if self.name == "error":
            self.description.append(
                "Errors are also handled in the same way as built-in errors. They are collected to errors.json, printed with metadata, etc."
            )
        self.match_qualifiers.append("once")
        self.match_qualifiers.append("onchange")
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
        #
        # jan 29: added None to actuals. stop().to_value() is None. there's a note in stop()
        # this may need a rethink.
        #
        a.arg(
            name="eval",
            types=[None, Function, Equality],
            actuals=[None, Any],
        )
        self.args.validate(self.siblings_or_equality())
        if self.name == "error":
            c = self._child_two()
            if isinstance(c, Term):
                msg = "error() only takes one string argument"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise ChildrenException(msg)
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
                    if self.name == "error":
                        self.matcher.csvpath.error_manager.handle_error(
                            source=self, msg=f"{v}"
                        )
                    else:
                        self.matcher.csvpath.print(f"{v}")
                    if right is not None:
                        right.matches(skip=skip)
                if self.once:
                    self._set_has_happened()
        self.match = self.default_match()
