# pylint: disable=C0114
from .function import Function
import datetime


class Now(Function):
    """returns the current datetime"""

    def check_valid(self) -> None:
        self.validate_zero_or_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        format = None
        if len(self.children) == 1:
            format = self.children[0].to_value(skip=skip)
            format = f"{format}".strip()
        x = datetime.datetime.now()
        xs = None
        if format:
            xs = x.strftime(format)
        else:
            xs = f"{x}"
        self.value = xs

    def matches(self, *, skip=None) -> bool:
        return self._noop_match()  # pragma: no cover
