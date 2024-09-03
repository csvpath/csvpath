# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import Term, ChildrenException, Equality, DataException
from csvpath import ConfigurationException


class HeaderNamesMismatch(Function):
    """
    given a delimited list of headers, checks that they all exist and
    optionally are in the same order
    """

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
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

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            self.matches = self.to_value(skip=skip)
        return self.match
