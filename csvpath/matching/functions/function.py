# pylint: disable=C0114
from typing import Any
from ..productions.matchable import Matchable
from .validation import Validation


class Function(Validation):
    """base class for all functions"""

    def __init__(self, matcher: Any, name: str, child: Matchable = None) -> None:
        super().__init__(matcher, name=name)
        self.matcher = matcher
        self._function_or_equality = child
        if child:
            self.add_child(child)

    def __str__(self) -> str:
        scn = self._simple_class_name()
        foe = self._function_or_equality
        return f"""{scn}.{self.qualified_name}({foe if foe is not None else ""})"""

    def reset(self) -> None:
        self.value = None
        self.match = None
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
            if self.do_onmatch():
                # if not self.onmatch or self.line_matches():
                self.matcher.csvpath.logger.debug(
                    "%s, a %s, calling produce value", self, self.FOCUS
                )
                self._produce_value(skip=skip)
            else:
                self._apply_default_value()
                self.matcher.csvpath.logger.debug(
                    f"@{self}: appling default value, {self.value}, because !do_onmatch"
                )
        return self.value

    def matches(self, *, skip=None) -> bool:
        if not skip:
            skip = []
        if self in skip:  # pragma: no cover
            return self._noop_match()
        if self.do_frozen():
            # doing frozen means not doing anything else. this is the
            # inverse of onmatch and other qualifiers. but it makes sense
            # and we're not talking about a qualifier, in any case. the
            # csvpath writer doesn't know anything about this.
            self.matcher.csvpath.logger.debug("We're frozen in %s", self)
            return self._noop_value()
        if not self.match:
            if self.do_onmatch():
                self.matcher.csvpath.logger.debug(
                    "%s, a %s, calling decide match", self, self.FOCUS
                )
                self._decide_match(skip=skip)
                self.matcher.csvpath.logger.debug(
                    "Function.matches _decide_match returned %s", self.match
                )
            else:
                self._apply_default_match()
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

    def _apply_default_match(self) -> bool:
        """provides the default when to_match is not producing a value.
        subclasses may override this method if they need a different
        default.
        """
        self.match = self.default_match()
        self.matcher.csvpath.logger.debug(
            "%s applying default match: %s", self, self.match
        )
