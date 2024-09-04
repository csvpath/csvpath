# pylint: disable=C0114
from .function import Function


class CountHeaders(Function):
    """returns the current number of headers expected or
    the actual number of headers in a given line"""

    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        if self.name == "count_headers":
            ret = len(self.matcher.csvpath.headers)
            self.value = ret
        elif self.name == "count_headers_in_line":
            self.value = len(self.matcher.line)
