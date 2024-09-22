# pylint: disable=C0114
from typing import Any
from ..function_focus import SideEffect


class Stopper(SideEffect):
    def check_valid(self) -> None:
        self.validate_zero_or_more_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self._apply_default_value()

    def _stop_me(self, skip=None):
        stopped = False
        if len(self.children) == 1:
            b = self.children[0].matches(skip=skip)
            if b is True:
                self.matcher.csvpath.stop()
                pln = self.matcher.csvpath.line_monitor.physical_line_number
                self.matcher.csvpath.logger.info(
                    f"stopping at {pln}. contained child matches."
                )
                stopped = True
        else:
            self.matcher.csvpath.stop()
            pln = self.matcher.csvpath.line_monitor.physical_line_number
            self.matcher.csvpath.logger.info(f"stopping at {pln}")
            stopped = True
        if stopped and self.name == "fail_and_stop":
            self.matcher.csvpath.logger.info("setting invalid")
            self.matcher.csvpath.is_valid = False


class Stop(Stopper):
    """when called halts the scan. the current row will be returned."""

    def _decide_match(self, skip=None) -> None:
        self.match = True
        self._stop_me(skip=skip)


class StopAll(Stopper):
    """when called halts the scan. the current row will be returned."""

    def _decide_match(self, skip=None) -> None:
        self.match = True
        self._stop_me(skip=skip)
        if self.matcher.csvpath.csvpaths:
            self.matcher.csvpath.csvpaths.stop_all()


class Skipper(SideEffect):
    def check_valid(self) -> None:
        self.validate_zero_or_more_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self._apply_default_value()

    def _skip_me(self, skip=None):
        if len(self.children) == 1:
            b = self.children[0].matches(skip=skip)
            if b is True:
                self.matcher.skip = True
                if self.once:
                    self._set_has_happened()
                pln = self.matcher.csvpath.line_monitor.physical_line_number
                self.matcher.csvpath.logger.info(
                    f"skipping physical line {pln}. contained child matches."
                )
        else:
            self.matcher.skip = True
            if self.once:
                self._set_has_happened()
            pln = self.matcher.csvpath.line_monitor.physical_line_number
            self.matcher.csvpath.logger.info(f"skipping line {pln}")


class Skip(Skipper):
    """skips to the next line. will probably leave later match components
    unconsidered; although, there is not certainty that will happen."""

    def _decide_match(self, skip=None) -> None:
        if self.do_once():
            self._skip_me(skip=skip)
        self.match = self.default_match()


class SkipAll(Skipper):
    """skips to the next line. tells the CsvPaths instance, if any,
    to skip all the following CsvPath instances as well.
    Note: skip_all() is only for the parallel/breadth-first methods.
    for the serial/paths methods skip_all() works the same as skip().
    """

    def check_valid(self) -> None:
        self.validate_zero_or_more_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        if self.do_once():
            self._skip_me(skip=skip)
            if self.matcher.csvpath.csvpaths:
                self.matcher.csvpath.csvpaths.skip_all()
        self.match = self.default_match()
