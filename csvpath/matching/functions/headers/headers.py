# pylint: disable=C0114
from ..function_focus import MatchDecider


class Headers(MatchDecider):
    """directs functions like any() to look in the headers.
    secondary purpose: do existence test for a header name or
    index for the current headers/whole file. header_name
    doesn't quite do this so we'll keep the function here.
    """

    def check_valid(self) -> None:
        self.validate_zero_or_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        if len(self.children) == 1:
            v = self.children[0].to_value()
            if isinstance(v, int) or v.isdigit():
                i = int(v)
                if i < 0 or i >= len(self.matcher.csvpath.headers):
                    self.match = False
                else:
                    self.match = True
            else:
                self.match = self.matcher.header_index(v) is not None
        else:
            self.match = self._apply_default_match()  # pragma: no cover
