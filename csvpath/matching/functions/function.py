# pylint: disable=C0114
from typing import Any
from ..productions.matchable import Matchable


class Function(Matchable):
    """base class for all functions"""

    def __init__(self, matcher: Any, name: str, child: Matchable = None) -> None:
        super().__init__(matcher, name=name)
        self.matcher = matcher
        self._function_or_equality = child
        self.args = None
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
            self.args.matched = None
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
            return self._noop_value()
        if self.do_frozen():
            # doing frozen means not doing anything else. this is the
            # inverse of onmatch and other qualifiers. but it makes sense
            # and we're not talking about a qualifier, in any case. the
            # csvpath writer doesn't know anything about this.
            self.matcher.csvpath.logger.debug("We're frozen in %s", self)
            return self._noop_value()
        if self.value is None:
            # count() doesn't yet use args. it is grandfathered, for now.
            if self.args and not self.args.matched:
                self.matcher.csvpath.logger.debug(
                    "Validating arg actuals for %s in to_value", self.name
                )
                self.args.matches(self.sibling_values(skip=skip))
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
        return self.value

    def matches(self, *, skip=None) -> bool:
        if not skip:
            skip = []
        if self in skip:  # pragma: no cover
            return self.default_match()
        if self.do_frozen():
            # doing frozen means not doing anything else. this is the
            # inverse of onmatch and other qualifiers. but it makes sense
            # and we're not talking about a qualifier, in any case. the
            # csvpath writer doesn't know anything about this.
            self.matcher.csvpath.logger.debug("We're frozen in %s", self)
            return self._noop_value()
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
                    # why did vvvv break counter() and other funcs?
                    # in the case of gt() we were disallowing None. not validating on
                    # matches allowed us to never see a None. however, None > x is                                  # a valid comparison, for us, equaling False. had to adjust the
                    # validation. the missing matches validation was in equality --
                    # the -> only called matches allowing some match components to
                    # never be validated.
                    #
                    self.args.matches(self.sibling_values(skip=skip))
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
                self._decide_match(skip=skip)
                self.matcher.csvpath.logger.debug(
                    "Function.matches _decide_match returned %s", self.match
                )
            else:
                self.match = self.default_match()
                self.matcher.csvpath.logger.debug(
                    f"@{self}: appling default match, {self.match}, because !do_onmatch"
                )
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
