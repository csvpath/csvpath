# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import Header, Variable

#
# TODO: when we have functions.header() sorted out (to headers())
# it should be possible to use it to request a check of all
# headers.
#


class Empty(Function):
    def check_valid(self) -> None:
        self.validate_one_arg([Header, Variable])
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            self.value = self.matches(skip=skip)
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            v = self.children[0].to_value()
            ab = self.children[0].asbool
            if ab:
                try:
                    v = bool(v)
                    self.match = v
                except Exception:
                    #
                    # TODO: use ExpressionUtility.asbool. note it existence tests different.
                    #
                    self.matcher.csvpath.logger.warning(
                        f"Cannot convert {v} to bool; therefore the asbool match is False"
                    )
                    self.match = False
            elif v is None:
                self.match = True
            elif isinstance(v, list) and len(v) == 0:
                self.match = True
            elif isinstance(v, dict) and len(dict) == 0:
                self.match = True
            elif isinstance(v, tuple) and len(v) == 0:
                self.match = True
            elif isinstance(v, str) and v.strip() == "":
                self.match = True
            else:
                self.match = False
        return self.match
