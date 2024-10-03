# pylint: disable=C0114
from typing import Any
from ..function_focus import MatchDecider
from ..args import Args
from csvpath.matching.productions.variable import Variable
from csvpath.matching.functions.function import Function
from csvpath.matching.productions.equality import Equality


class Last(MatchDecider):
    """matches on the last line that will be scanned. last() will always run."""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        #
        # we don't expect or use a value, but we don't care if one is generated
        #
        self.args.argset(1).arg(
            types=[None, Function, Variable, Equality], actuals=[None, Any]
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def override_frozen(self) -> bool:
        """fail() and last() must override to return True so that we execute them even on
        an otherwise skipped last line.
        """
        self.matcher.csvpath.logger.info(
            f"Last.override_frozen: overriding frozen in {self}"
        )
        return True

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
            self.match = True
        else:
            self.match = False
        if self.match:
            if len(self.children) == 1:
                self.matcher.csvpath.logger.debug(
                    "Overriding frozen in last(): %s", self
                )
                self.matcher.csvpath.is_frozen = False
                self.children[0].matches(skip=[self])
                self.matcher.csvpath.is_frozen = True
                self.matcher.csvpath.logger.debug(
                    "Resetting frozen after last(): %s", self
                )
