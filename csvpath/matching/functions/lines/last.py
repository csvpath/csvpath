# pylint: disable=C0114
from ..function_focus import MatchDecider


class Last(MatchDecider):
    """matches on the last line that will be scanned. last() will always run."""

    def check_valid(self) -> None:
        self.validate_zero_or_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        last = self.matcher.csvpath.line_monitor.is_last_line()
        last_scan = (
            self.matcher.csvpath.scanner
            and self.matcher.csvpath.scanner.is_last(
                self.matcher.csvpath.line_monitor.physical_line_number
            )
        )
        if last or last_scan:
            if not self.onmatch or self.line_matches():
                self.match = True
                if self.match:
                    if len(self.children) == 1:
                        self.children[0].matches(skip=[self])
            else:
                self.match = False
        else:
            self.match = False
