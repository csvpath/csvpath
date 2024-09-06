# pylint: disable=C0114
from csvpath.matching.util.exceptions import DataException
from ..function_focus import ValueProducer


class HeaderName(ValueProducer):
    """looks up a header name by index or an index by header name
    if given an expected result as a 2nd argument we return
    True/False on the match of expected to actual

    if we don't have an actual, the match is an existance test for the
    header, not the line value of the header. this means this function
    overlaps the old header function, but adds more value.
    """

    def check_valid(self) -> None:
        self.validate_one_or_two_args()
        super().check_valid()

    def _decide_match(self, skip=None) -> None:
        v = self.to_value()
        ret = None
        if v is None:
            ret = False
        elif isinstance(v, bool):
            ret = v
        elif type(v) in [int, str]:
            ret = True
        else:
            raise DataException("Unexpected value returned: {v}.")
        self.match = ret

    def _produce_value(self, skip=None) -> None:
        v = self._value_one(skip=skip)
        expected = self._value_two(skip=skip)
        actual = self._look_up_header(v)
        if expected is None:
            self.value = actual
        else:
            self.value = self._header_matches(actual, expected)
            if self.name == "header_name_mismatch":
                self.value = not self.value

    def _header_matches(self, actual, expected):
        if actual is None:
            return False
        return actual == expected

    def _look_up_header(self, v):
        ret = None
        if isinstance(v, int) or f"{v}".strip().lower().isdigit():
            ret = self._header_for_int(v)
        else:
            ret = self.matcher.header_index(v)
        return ret

    def _header_for_int(self, v):
        i = int(v)
        if i < 0:
            hlen = len(self.matcher.csvpath.headers)
            c = hlen + i
            if i < 0:
                c = c - 1
            i = c
        hname = self.matcher.header_name(i)
        return hname
