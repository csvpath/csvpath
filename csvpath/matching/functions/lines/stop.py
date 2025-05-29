# pylint: disable=C0114
from typing import Any
from ..function_focus import SideEffect
from csvpath.matching.productions import Header, Variable, Equality
from csvpath.matching.functions.function import Function
from ..args import Args


class Stopper(SideEffect):
    def check_valid(self) -> None:
        self.description = None
        if self.name == "stop":
            self.description = [
                self._cap_name(),
                self.wrap(
                    """\
                        Halts the run abruptly.

                        When stop() contains no other match components it simply stops the run.

                        When stop contains another match component, stop() is conditional to its
                        evaluation. In this way stop() functions like a when/do expression.
                        This functionality convenient in some cases and adds additional composability.

                        stop() will not necessarily prevent other match components in its
                        csvpath from being evaluated. Match components that come earlier in the
                        csvpath will be evaluated as normal. Match components that have the onmatch
                        qualifier are evaluated at the end of the csvpath, and so might not be
                        evaluated when stop() happens even if they come before stop().
                """
                ),
            ]
        elif self.name == "stop_all":
            self.description = [
                self._cap_name(),
                self.wrap(
                    """\
                        Halts the containing csvpath's run abruptly and, in certain
                        named-paths group runs, prevents subsequent csvpaths from running.

                        stop_all() shuts down a whole named-paths group run when the run method is
                        either breadth-first or the iterative programmatic next_paths() method.
                        Breadth-first runs are triggered with the collect_by_line(),
                        fast_forward_by_line(), and next_by_line() methods.

                        See stop() for more behavior details.
                """
                ),
            ]

        self.args = Args(matchable=self)
        self.args.argset(1).arg(
            name="eval this", types=[None, Function, Equality], actuals=[None, Any]
        )
        self.args.validate(self.siblings_or_equality())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        #
        # the default value is None. not sure that's ideal here. print will call
        # matches when it finds a stop (or anything) but validation calls
        # to_value. that means we might think in terms of bool, but we have to
        # define including None. open question. :/
        #
        # self.value = self.matches(skip=skip)
        self._apply_default_value()

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
        self._stop_me(skip=skip)
        self.match = self.default_match()


class StopAll(Stopper):
    """when called halts the scan. the current row will be returned."""

    def _decide_match(self, skip=None) -> None:
        self._stop_me(skip=skip)
        if self.matcher.csvpath.csvpaths:
            self.matcher.csvpath.csvpaths.stop_all()
        self.match = self.default_match()


class Skipper(SideEffect):
    def check_valid(self) -> None:
        self.description = None
        if self.name == "skip":
            self.description = [
                self._cap_name(),
                self.wrap(
                    """\
                        Jumps to the next line abruptly.

                        skip() short-circuits the full csvpath evaluation
                        of a line. Earlier match components will be evaluated; although, with
                        the exception of any components carrying the onmatch qualifier, which
                        pushes them to the back of the csvpath processing order.

                        Like stop(), skip() can optionally take a function argument that will determine if
                        skip() is triggered. In this way, skip() acts as if it has an embedded
                        when/do operator.
                """
                ),
            ]
        elif self.name == "skip_all":
            self.description = [
                self._cap_name(),
                self.wrap(
                    """\
                        Jumps to the next line abruptly. In a named-paths group run, where the
                        run method is breadth-first, skip_all() jumps to the next line without
                        any following csvpaths seeing the line at all.

                        A breadth-first run method is one of collect_by_line(),
                        fast_forward_by_line, or next_by_line(). These methods pass each line through
                        all csvpaths in the named-paths group before continuing to the next line.

                        skip_all() short-circuits the full csvpath evaluation
                        of a line. Earlier match components will be evaluated; although, with
                        the exception of any components carrying the onmatch qualifier, which
                        pushes them to the back of the csvpath processing order.

                        See skip() for more behavior details.
            """
                ),
            ]
        self.match_qualifiers.append("once")
        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.argset(1).arg(
            name="eval this", types=[Function, Equality], actuals=[None, Any]
        )
        self.args.validate(self.siblings_or_equality())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _skip_me(self, skip=None):
        if len(self.children) == 1:
            b = self.children[0].matches(skip=skip)
            if b is True:
                self.matcher.skip = True
                if self.name == "take":
                    self.matcher.take = True
                if self.once:
                    self._set_has_happened()
                pln = self.matcher.csvpath.line_monitor.physical_line_number
                self.matcher.csvpath.logger.info(
                    f"skipping physical line {pln}. contained child matches."
                )
        else:
            self.matcher.skip = True
            if self.name == "take":
                self.matcher.take = True
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

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        if self.do_once():
            self._skip_me(skip=skip)
            if self.matcher.csvpath.csvpaths:
                self.matcher.csvpath.csvpaths.skip_all()
        self.match = self.default_match()
