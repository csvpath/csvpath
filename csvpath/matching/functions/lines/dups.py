# pylint: disable=C0114
import hashlib
from csvpath.matching.productions import Header, Equality
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import MatchDecider


class HasDups(MatchDecider):
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

    def _decide_match(self, skip=None) -> None:
        if not self.onmatch or self.line_matches():
            ls = self.to_value()
            if len(ls) > 0:
                self.match = True
            else:
                self.match = False
