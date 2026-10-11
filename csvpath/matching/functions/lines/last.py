# pylint: disable=C0114
from typing import Any
from ..function_focus import MatchDecider
from ..args import Args
from csvpath.matching.productions.variable import Variable
from csvpath.matching.functions.function import Function
from csvpath.matching.productions.equality import Equality


class Last(MatchDecider):
    """matches on the last scanned line with data. last() will always run."""

    #
    # last()'s argument must only run on the last line. validating its
    # actual value would compute it on every line, and for e.g. and() or
    # or() computing the value runs their children, side effects and all.
    # the actual is declared Any, so there is nothing to validate (#326).
    #
    VALIDATES_ARG_ACTUALS = False

    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                    Evaluates True on the last line to be scanned that has data.
                    Trailing blank lines do not count.

                    last() used by itself will always run, even if its line turns out to be
                    blank and would otherwise be skipped. When last() is composed within other
                    functions it loses that ability to run no matter what. For e.g.
                    last() -> print("will always run")
                    vs.
                    and(yes(), last()) -> print("runs if the last scanned line is not blank")

                    Optionally, last() can take a function that will be evaluated when last()
                    evaluates to True. This function, if provided, will not necessarily be the
                    last evaluation of the run, but will happen only on the last line. At this
                    time a last() that has an encapsulated function will correctly run on the
                    last line but it will not produce True in assignment. Changing that behavior
                    is on the todo list. It should not be relied on.
            """
            ),
        ]
        self.args = Args(matchable=self)
        #
        # we don't expect or use a value, but we don't care if one is generated
        #
        self.args.argset(1).arg(
            name="eval on last",
            types=[None, Function, Variable, Equality],
            actuals=[None, Any],
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
        #
        # last() is true on the last line that is both scanned and has data,
        # so trailing blank lines do not move it (#308). if no line with data
        # is scanned at all, e.g. a header-only file scanned with $[1*], it is
        # true on the frozen last line instead (#306). either way it is true
        # on one line only.
        #
        csvpath = self.matcher.csvpath
        line_number = csvpath.line_monitor.physical_line_number
        last_data = csvpath.scanner is not None and (
            csvpath.scanner.is_last_scanned_data_line(line_number)
        )
        fallback = csvpath.is_lasts_only_line(self.matcher.line) and (
            csvpath._last_fired_on in (None, line_number)
        )
        if last_data or fallback:
            self.match = True
            csvpath._last_fired_on = line_number
        else:
            self.match = False
        if self.match:
            if len(self.children) == 1:
                self.matcher.csvpath.logger.debug(
                    "Overriding frozen in last(): %s", self
                )
                # disable frozen so we can eval, remembering the state so it
                # can be restored rather than forced on (#324)
                was_frozen = self.matcher.csvpath.is_frozen
                self.matcher.csvpath.is_frozen = False
                # we do not take any match value returned
                self.children[0].matches(skip=[self])
                # restore frozen
                self.matcher.csvpath.is_frozen = was_frozen
                self.matcher.csvpath.logger.debug("Reset frozen after last(): %s", self)
