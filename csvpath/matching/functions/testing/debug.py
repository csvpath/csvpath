# pylint: disable=C0114
import datetime
from ..function_focus import SideEffect
from csvpath.util.log_utility import LogUtility
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.productions import Equality


class Debug(SideEffect):
    """sets the logging level"""

    def check_valid(self) -> None:
        self.validate_zero_or_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        level = None
        if len(self.children) == 1:
            level = self.children[0].to_value(skip=skip)
            level = f"{level}".strip()
        else:
            level = "debug"
        LogUtility.logger(self.matcher.csvpath, level)


class BriefStackTrace(SideEffect):
    def check_valid(self) -> None:
        self.validate_zero_or_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        out = None
        if len(self.children) == 1:
            out = self.children[0].to_value(skip=skip)
            out = f"{out}".strip()
            if out not in ["log", "print"]:
                out = "log"
        else:
            out = "log"
        if out == "log":
            LogUtility.log_brief_trace(self.matcher.csvpath.logger)
        else:
            LogUtility.log_brief_trace()


class VoteStack(SideEffect):
    def check_valid(self) -> None:
        self.validate_zero_args()
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
        self.validate_zero_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        votes = []
        dowhens = self._find_do_whens()
        for c in dowhens:
            votes.append(c.DO_WHEN)
        self.value = votes

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()

    def _find_do_whens(self) -> None:
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
        return dowhens
