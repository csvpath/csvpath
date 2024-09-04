# pylint: disable=C0114
import datetime
from .function import Function


class Now(Function):
    """returns the current datetime"""

    def check_valid(self) -> None:
        self.validate_zero_or_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        form = None
        if len(self.children) == 1:
            form = self.children[0].to_value(skip=skip)
            form = f"{form}".strip()
        x = datetime.datetime.now()
        xs = None
        if form:
            xs = x.strftime(form)
        else:
            xs = f"{x}"
        self.value = xs

    def matches(self, *, skip=None) -> bool:
        return self._noop_match()  # pragma: no cover
