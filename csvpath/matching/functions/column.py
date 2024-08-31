from typing import Any
from .function import Function
from ..productions import Term, ChildrenException, Equality, DataException
from csvpath import ConfigurationException


class Column(Function):
    """depreciated. the word column is confusing since
    CsvPath takes a position on the words column vs. header.
    This was one of the few places the word was used regularly.
    we also wanted the additional functionality in HeaderName
    so it is time to phase Column out.
    """

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if not self.value:
            v = self.children[0].to_value()
            if isinstance(v, int) or v.isdigit():
                i = int(v)
                if i < 0:
                    hlen = len(self.matcher.csvpath.headers)
                    c = hlen + i
                    if i < 0:
                        c = c - 1
                    i = c
                self.value = self.matcher.header_name(i)
            else:
                self.value = self.matcher.header_index(v)
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return self._noop_match()  # pragma: no cover


class HeaderNamesMismatch(Function):
    """
    given a delimited list of headers, checks that they all exist and
    optionally are in the same order
    """

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if not self.value:
            varname = self.first_non_term_qualifier(self.name)
            present = self.matcher.get_variable(f"{varname}_present")
            if present and len(present) == len(self.matcher.csvpath.headers):
                self.value = True
            elif present:
                self.value = False
            else:
                header_names = self._value_one()
                names = header_names.split("|")
                present = []
                unmatched = []
                misordered = []
                duplicated = []
                for i, name in enumerate(names):
                    name = name.strip()
                    found = False
                    for j, header in enumerate(self.matcher.csvpath.headers):
                        if name == header:
                            found = True
                            if i == j:
                                present.append(header)
                            else:
                                if header in misordered or header in present:
                                    if header not in duplicated:
                                        duplicated.append(header)
                                if header not in misordered:
                                    misordered.append(header)
                    if found is False:
                        unmatched.append(name)
                if len(present) != len(self.matcher.csvpath.headers):
                    for name in self.matcher.csvpath.headers:
                        if name not in names:
                            unmatched.append(name)
                self.matcher.set_variable(f"{varname}_present", value=present)
                self.matcher.set_variable(f"{varname}_unmatched", value=unmatched)
                self.matcher.set_variable(f"{varname}_misordered", value=misordered)
                self.matcher.set_variable(f"{varname}_duplicated", value=duplicated)
                self.value = len(present) != len(self.matcher.csvpath.headers)
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return self._noop_match()  # pragma: no cover
        if self.match is None:
            self.matches = self.to_value(skip=skip)
        return self.match


class HeaderName(Function):
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

    def _header_matches(self, actual, expected):
        if actual is None:
            return False
        else:
            return actual == expected

    def _look_up_header(self, v):
        ret = None
        if isinstance(v, int) or f"{v}".strip().lower().isdigit():
            ret = self._header_for_int(v)
        else:
            ret = self.matcher.header_index(v)
        return ret

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if not self.value:
            v = self._value_one()
            expected = self._value_two()
            actual = self._look_up_header(v)
            if expected is None:
                self.value = actual
            else:
                self.value = self._header_matches(actual, expected)
                if self.name == "header_name_mismatch":
                    self.value = not self.value
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return self._noop_match()  # pragma: no cover
        if self.match is None:
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
        return self.match
