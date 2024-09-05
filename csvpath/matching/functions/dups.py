# pylint: disable=C0114
import hashlib
from .function import Function
from ..productions import Header, Equality
from ..util.exceptions import ChildrenException


class HasDups(Function):
    """checks for duplicate lines, in whole or part, by hashing."""

    def check_valid(self) -> None:
        self.validate_zero_or_more_args(types=[Header])
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        name = self.first_non_term_qualifier(self.name)
        values = self.matcher.get_variable(name, set_if_none={})
        string = ""
        fingerprint = None
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
        values[fingerprint].append(
            self.matcher.csvpath.line_monitor.physical_line_number
        )
        self.matcher.set_variable(name, value=values)

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            self._noop_match()
        if self.match is None:
            if not self.onmatch or self.line_matches():
                ls = self.to_value()
                if len(ls) > 0:
                    self.match = True
                else:
                    self.match = False
        return self.match  # pragma: no cover
