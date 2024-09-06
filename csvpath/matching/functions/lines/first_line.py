# pylint: disable=C0114
from csvpath.matching.productions import Equality
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import MatchDecider
from ..function import Function


class FirstLine(MatchDecider):
    """True when on the first line, scan, or match"""

    def check_valid(self) -> None:
        self.validate_zero_or_one_arg(types=[Function, Equality])
        if len(self.children) == 1 and isinstance(self.children[0], Equality):
            if not self.children[0].op == "=":
                raise ChildrenException(
                    "Child can only be either a function or a variable assignment"
                )
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.match(skip=skip)

    def _decide_match(self, skip=None) -> None:
        t = self.name
        if t == "firstmatch":
            if self.matcher.csvpath.match_count == 0 and self.line_matches():  # 1-based
                self.match = True
            else:
                self.match = False
        elif t == "firstscan":
            self.match = (
                self.matcher.csvpath.scan_count == 1
            )  # 1-based, set before matcher is called.
        elif t == "firstline":
            self.match = (
                self.matcher.csvpath.line_monitor.data_line_number == 0
            )  # 0-based, updated after matcher is called.
        else:
            raise ChildrenException(f"Unknown type of line: {t}")
        if self.match:
            if len(self.children) == 1:
                child = self.children[0]
                child.matches(skip=skip)
