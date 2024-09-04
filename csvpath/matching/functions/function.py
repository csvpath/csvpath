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
        return f"""{self._simple_class_name()}.{self.name}({self._function_or_equality if self._function_or_equality is not None else ""})"""

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
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            if not self.onmatch or self.line_matches():
                self._produce_value(skip=skip)
            else:
                self._get_default_value()
        return self.value

    def _produce_value(self, skip=None) -> None:
        pass

    def _get_default_value(self) -> None:
        """provides the default when to_value is not producing a value.
        subclasses may override this method if they need a different
        default. e.g. sum() requires the default to be the running sum
        -- not updated; the then current summation -- when the logic
        in its _produce_value doesn't obtain.
        """
        self.value = None
