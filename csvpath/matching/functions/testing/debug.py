# pylint: disable=C0114
import datetime
import logging
from typing import Any
from ..function_focus import SideEffect
from csvpath.util.log_utility import LogUtility
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.productions import Equality
from csvpath.matching.productions.term import Term
from csvpath.matching.productions.variable import Variable
from csvpath.matching.functions.function import Function
from csvpath.matching.productions.header import Header
from ..args import Args


class Log(SideEffect):
    """logs a msg at a log level, defaulting to info"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                   Writes a message to the CsvPath Framework log at a certain log level.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(name="log this", types=[Term], actuals=[str])
        a.arg(name="info, debug, warn, error", types=[None, Term], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        msg = self._value_one(skip=skip)
        level = self._value_two(skip=skip)
        if level in [None, "info"]:
            self.matcher.csvpath.logger.info(msg)
        elif level == "debug":
            self.matcher.csvpath.logger.debug(msg)
        elif level in ["warn", "warning"]:
            self.matcher.csvpath.logger.warning(msg)
        elif level == "error":
            self.matcher.csvpath.logger.error(msg)
        else:
            self.matcher.csvpath.logger.info(msg)
        self.match = self.default_match()


class Debug(SideEffect):
    """sets the logging level"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                   Sets the CsvPath Framework log level.

                   The level is set for the CsvPath class, not the CsvPaths class. That
                   means the log level is changed for particular csvpath currently running,
                   not any other csvpaths running after or along-side in a breadth-first
                   configuration.
                """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.argset(1).arg(
            name="info, debug, warn, error",
            types=[None, Term, Function, Variable, Header],
            actuals=[None, str],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        level = None
        if len(self.children) == 1:
            level = self.children[0].to_value(skip=skip)
            level = f"{level}".strip()
        else:
            level = "debug"
        logger = LogUtility.logger(self.matcher.csvpath, level)
        self.matcher.csvpath.logger = logger
        self.match = self.default_match()


class BriefStackTrace(SideEffect):
    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                   Writes a shallow stack trace to the log or to print().

                   If a second argument, either 'log' or 'print', is not provided the default
                   is to print to the default printout stream.
                """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.argset(1).arg(
            types=[None, Term, Function, Variable, Header], actuals=[None, str]
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        out = None
        if len(self.children) == 1:
            out = self.children[0].to_value(skip=skip)
            out = f"{out}".strip()
            if out not in ["log", "print"]:
                out = "log"
        else:
            out = "print"
        if out == "log":
            LogUtility.log_brief_trace(logger=self.matcher.csvpath.logger)
        else:
            LogUtility.log_brief_trace(printer=self.matcher.csvpath)


class VoteStack(SideEffect):
    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Returns the votes of the match components for each line as a stack.

                    The votes are collected from the central record, not from
                    each component directly. This means that any match components that
                    have not yet voted will return None, rather than True or False. This
                    is most noticable when you are printing the vote stack. The print function,
                    not having voted until it is complete, always returns None.
                """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        # do this first so we get an complete vote tally
        self.matches(skip=skip)
        votes = []
        # we're being evaluated so we should assume our expression hasn't
        # voted yet. while we could be embedded somewhere deep the expectation
        # is that we're the main element of our match component, so we should
        # be able to represent a ~faux vote without causing problems.
        me = ExpressionUtility.get_my_expression(self)
        for e in self.matcher.expressions:
            if e[0] == me:
                votes.append(self.match)
            else:
                votes.append(e[1])
        self.value = votes

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()


class DoWhenStack(SideEffect):
    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Returns a stack of bool representing the when/do operators for each line.

                    Those when/do operators that were triggered have a True. Those that didn't fire have a False.
                """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()

    def _produce_value(self, skip=None) -> None:
        votes = []
        dowhens = self._find_do_when_children()
        for c in dowhens:
            votes.append(c.DO_WHEN)
        self.value = votes

    def _find_do_when_children(self):
        self.matcher.csvpath.logger.debug("Looking for do-whens")
        dowhens = []
        cs = []
        for es in self.matcher.expressions:
            cs.append(es[0])
        while len(cs) > 0:
            c = cs.pop()
            if isinstance(c, Equality) and c.op == "->":
                dowhens.append(c)
            cs += c.children
        dowhens.reverse()
        self.matcher.csvpath.logger.debug(f"Found {len(dowhens)} do-whens")
        return dowhens
