# pylint: disable=C0114
from typing import Any
from csvpath.matching.productions import Equality
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import MatchDecider
from ..function import Function
from ..args import Args


class FirstLine(MatchDecider):
    """True when on the first line, scan, or match"""

    def check_valid(self) -> None:
        if self.name in ["firstline", "first_line"]:
            self.aliases = ["firstline", "first_line"]
        elif self.name in ["firstscan", "first_scan"]:
            self.aliases = ["firstscan", "first_scan"]
        elif self.name in ["firstmatch", "first_match"]:
            self.aliases = ["firstmatch", "first_match"]
        self.args = Args(matchable=self)
        self.args.argset(1).arg(types=[None, Function, Equality], actuals=[None, Any])
        self.args.validate(self.siblings())
        if len(self.children) == 1 and isinstance(self.children[0], Equality):
            if not self.children[0].op == "=":
                # correct as structure / children exception
                msg = "Child can only be either a function or a variable assignment"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise ChildrenException(msg)

        if self.name not in ["firstmatch", "firstscan", "firstline"]:
            # correct as structure / children exception
            msg = f"Unknown function name: {self.name}"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise ChildrenException(msg)
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        t = self.name
        if t in ["firstmatch", "first_match"]:
            if self.matcher.csvpath.match_count == 0 and self.line_matches():  # 1-based
                self.match = True
            else:
                self.match = False
        elif t in ["firstscan", "first_scan"]:
            self.match = (
                self.matcher.csvpath.scan_count == 1
            )  # 1-based, set before matcher is called.
        elif t in ["firstline", "first_line"]:
            self.match = (
                self.matcher.csvpath.line_monitor.data_line_number == 0
            )  # 0-based, updated after matcher is called.
        if self.match:
            if len(self.children) == 1:
                child = self.children[0]
                child.matches(skip=skip)
