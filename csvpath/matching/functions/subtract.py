# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import Equality, Term
from ..util.exceptions import DataException


class Subtract(Function):
    """subtracts numbers"""

    def check_valid(self) -> None:
        self.validate_one_or_more_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if not self.value:
            child = self.children[0]
            if isinstance(child, Term):
                v = child.to_value()
                v = int(v)
                #
                # do x = -1 * n to make negative
                #
                self.value = v * -1
            elif isinstance(child, Equality):
                self.value = self._do_sub(child, skip=skip)
        return self.value

    def _do_sub(self, child, skip=None):
        siblings = child.commas_to_list()
        ret = 0
        for i, sib in enumerate(siblings):
            v = sib.to_value(skip=skip)
            if i == 0:
                ret = v
            else:
                try:
                    ret = float(ret) - float(v)
                except Exception as ex:
                    err = DataException(f"{ex}")
                    err.datum = (ret, v)
                    # reset self.value just in case
                    self.value = None
                    raise err
        return ret

    def matches(self, *, skip=None) -> bool:
        return self._noop_match()  # pragma: no cover
