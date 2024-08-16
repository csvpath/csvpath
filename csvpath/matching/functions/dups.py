from typing import Any
from .function import Function, ChildrenException
from ..productions import Header, Equality
import hashlib


class HasDups(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            om = self.has_onmatch()
            if not om or self.line_matches():
                name = self.first_non_term_qualifier(self.name)
                values = self.matcher.get_variable(name, set_if_none={})
                string = ""
                fingerprint = None
                self.validate_zero_or_more_args(types=[Header])
                if len(self.children) == 1:
                    if isinstance(self.children[0], Equality):
                        siblings = self.children[0].commas_to_list()
                        for _ in siblings:
                            string += f"{_.to_value()}"
                    elif isinstance(self.children[0], Header):
                        string = f"{self.children[0].to_value()}"
                    else:
                        # should never get here
                        raise ChildrenException("has_dups must have header children")
                else:
                    for _ in self.matcher.line:
                        string += f"{_}"
                fingerprint = hashlib.sha256(string.encode("utf-8")).hexdigest()
                if fingerprint in values:
                    self.value = values[fingerprint]
                else:
                    self.value = []
                    values[fingerprint] = []
                values[fingerprint].append(self.matcher.csvpath.line_number)
                self.matcher.set_variable(name, value=values)
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            self._noop_match()
        if self.match is None:
            om = self.has_onmatch()
            if not om or self.line_matches():
                ls = self.to_value()
                if len(ls) > 0:
                    self.match = True
                else:
                    self.match = False
        return self.match  # pragma: no cover
