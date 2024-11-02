# pylint: disable=C0114
import traceback
import signal
import time
from typing import Any
from ..productions.matchable import Matchable
from ..util.exceptions import ChildrenException


class CheckedUnset:
    """pass on self.checked if setting self.value=None would not be clear/effective"""

    pass


class Function(Matchable):
    """base class for all functions"""

    def __init__(self, matcher: Any, name: str, child: Matchable = None) -> None:
        super().__init__(matcher, name=name)
        self.matcher = matcher
        self._function_or_equality = child
        self.args = None
        self.checked = None
        if child:
            self.add_child(child)

    def __str__(self) -> str:
        scn = self._simple_class_name()
        foe = self._function_or_equality
        return f"""{scn}.{self.qualified_name}({foe if foe is not None else ""})"""

    def reset(self) -> None:
        self.value = None
        self.match = None
        if self.args:
            self.args.reset()
        self.checked = None
        super().reset()

    def to_value(self, *, skip=None) -> bool:
        """implements a standard to_value. subclasses either override this
        method or provide an implementation of _produce_value. the latter
        is strongly preferred because that gives a uniform approach to
        on match, and probably other qualifiers. if the default value is
        not None, subclasses can optionally override _get_default_value.
        """
        if not skip:
            skip = []
        if self in skip:  # pragma: no cover
            ret = self._noop_value()
            self.valuing().result(ret).because("skip")
            return ret
        #
        # experiment -- timing
        #
        startval = time.perf_counter_ns()
        # exp end
        if self.do_frozen():
            # doing frozen means not doing anything else. this is the
            # inverse of onmatch and other qualifiers. but it makes sense
            # and we're not talking about a qualifier, in any case. the
            # csvpath writer doesn't know anything about this.
            self.matcher.csvpath.logger.debug("We're frozen in %s", self)
            return self._noop_value()
        if self.value is None and not isinstance(self.checked, CheckedUnset):
            # count() doesn't yet use args. it is grandfathered, for now.
            if self.args and not self.args.matched:
                self.matcher.csvpath.logger.debug(
                    "Validating arg actuals for %s in to_value", self.name
                )
                chk = len(self.my_expression.errors)
                self.args.matches(self.sibling_values(skip=skip))
                if chk < len(self.my_expression.errors):
                    # we have issues. return because nothing should work.
                    return self.value
            elif self.args:
                self.matcher.csvpath.logger.debug(
                    "Validation already done on arg actuals for %s in to_value",
                    self.name,
                )
            if self.do_onmatch():
                self.matcher.csvpath.logger.debug(
                    "%s, a %s, calling produce value", self, self.__class__.FOCUS
                )
                self._produce_value(skip=skip)
            else:
                self._apply_default_value()
                self.matcher.csvpath.logger.debug(
                    "@{self}: appling default value, {self.value}, because !do_onmatch"
                )
        # we strip because csvs generally don't consider whitespace before and
        # after the delimiter to be part of the data. unless they do. possibly
        # we should make this configurable. if so, it should be at the config.ini
        # and in comments. but... should we do it here at all?  makes sense for
        # Term and Header, but maybe not for Function?
        if isinstance(self.value, str):
            self.value = self.value.strip()
        #
        # experiment - timing
        #
        endval = time.perf_counter_ns()
        t = (endval - startval) / 1000000
        self.matcher.csvpath._up_function_time_value(self.__class__, t)
        #
        # exp end
        #
        return self.value

    def matches(self, *, skip=None) -> bool:
        if not skip:
            skip = []
        if self in skip:  # pragma: no cover
            ret = self.default_match()
            self.matching().result(ret).because("skip")
            return ret
        #
        # experiment -- timing
        #
        startmatch = time.perf_counter_ns()
        # exp end
        try:
            #
            #
            #
            if self.do_frozen():
                # doing frozen means not doing anything else. this is the
                # inverse of onmatch and other qualifiers. but it makes sense
                # and we're not talking about a qualifier, in any case. the
                # csvpath writer doesn't know anything about this.
                self.matcher.csvpath.logger.debug("We're frozen in %s", self)
                ret = self._noop_value()
                self.matching().result(ret).because("frozen")
                return ret
            if self.match is None:
                if self.do_onmatch():
                    #
                    # out of order (child before parent) seems like it would be a problem
                    # for some functions (e.g. print) that notionally do their thing and
                    # then do a child thing. in reality, i'm not sure this ever matters.
                    # skip, fail, stop, print don't need the ordering. there may be some
                    # i'm forgetting, but if there's a need for strict ordering we should
                    # probably consider a "post" qualifier to be more intentional about it.
                    #
                    # count() doesn't yet use args. it is grandfathered, for now.
                    if self.args and not self.args.matched:
                        self.matcher.csvpath.logger.debug(
                            "Validating arg actuals for %s in matches", self.name
                        )
                        #
                        # why did vvvv break counter() and other funcs? answer:
                        # in the case of gt() we were disallowing None. not validating on
                        # matches allowed us to never see a None. however, None > x is                                  # a valid comparison, for us, equaling False. had to adjust the
                        # validation. the missing matches validation was in equality --
                        # the -> only called matches allowing some match components to
                        # never be validated.
                        #
                        #
                        # we're collecting errors from child sibs and using sigint
                        # to indicate that a value couldn't be gotten and that this
                        # parent should raise an exception and stop. the point is
                        # to collect all the problems before stopping, rather than
                        # the user seeing problems one by one as they fix and retry.
                        # this obviously won't catch all errors. it doen't include
                        # the structure verification and rules created by the user.
                        #
                        sibs = self.sibling_values(skip=skip)
                        if Matchable.FAILED_VALUE in sibs:
                            # pln = self.matcher.csvpath.line_monitor.physical_line_number
                            self.raiseChildrenException(
                                f"Cannot continue with {self.my_chain} due to an invalid child"
                            )
                        #
                        # ready to run the match!
                        #
                        self.args.matches(sibs)

                    elif self.args:
                        self.matcher.csvpath.logger.debug(
                            "Validation already done on arg actuals for %s in matches",
                            self.name,
                        )
                    #
                    #
                    #
                    self.matcher.csvpath.logger.debug(
                        "%s, a %s, calling decide match", self, self.FOCUS
                    )
                    if (
                        self.args.args_match is False
                        and self.matcher.csvpath.stop_on_validation_errors
                    ):
                        self.matcher.csvpath.stop()
                    if (
                        self.args
                        and self.args.args_match is False
                        and self.matcher.csvpath.fail_on_validation_errors
                    ):
                        self.matcher.csvpath.is_valid = False
                    if (
                        self.args
                        and self.args.args_match is False
                        and self.matcher.csvpath._match_validation_errors is not None
                    ):
                        self.match = self.matcher.csvpath._match_validation_errors
                    else:
                        self._decide_match(skip=skip)
                        self.matcher.csvpath.logger.debug(
                            "Function.matches _decide_match returned %s", self.match
                        )
                        self.matching().result(self.match)
                else:
                    self.match = self.default_match()
                    self.matcher.csvpath.logger.debug(
                        f"@{self}: appling default match, {self.match}, because !do_onmatch"
                    )
                    self.matching().result(self.match).because("onmatch")
        except Exception as e:
            e.trace = traceback.format_exc()
            e.source = self
            e.json = self.to_json()
            self.my_expression.handle_error(e)
        #
        # experiment - timing
        #
        endmatch = time.perf_counter_ns()
        t = (endmatch - startmatch) / 1000000
        self.matcher.csvpath._up_function_time_match(self.__class__, t)
        #
        # exp end
        #
        return self.match

    def _produce_value(self, skip=None) -> None:
        pass

    def _decide_match(self, skip=None) -> None:
        pass

    def _apply_default_value(self) -> None:
        """provides the default when to_value is not producing a value.
        subclasses may override this method if they need a different
        default. e.g. sum() requires the default to be the running sum
        -- not updated; the then current summation -- when the logic
        in its _produce_value doesn't obtain.
        """
        self.value = None
        self.matcher.csvpath.logger.debug(
            "%s applying default value: %s", self, self.value
        )
