# pylint: disable=C0114
import hashlib
from csvpath.matching.productions import Header, Equality
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import MatchDecider, ValueProducer


#
# count dups produces a number of dups
# dup_lines produces a stack of line numbers
# has_dups decides match based on dups > 1
# all use fingerprinter to do the work
#
class CountDups(ValueProducer):
    """returns a count of duplicates."""

    def check_valid(self) -> None:
        self.validate_zero_or_more_args(types=[Header])
        super().check_valid()

    def _decide_match(self, skip=None) -> None:
        if self.name == "count_dups":
            self.match = self._apply_default_match()
        elif self.name == "has_dups":
            self.match == self.get_value(skip=skip) > 1

    def _produce_value(self, skip=None) -> None:
        name = self.first_non_term_qualifier(self.name)
        fingerprint, lines = FingerPrinter._capture_line(self, name, skip=skip)
        self.value = len(lines)


class HasDups(MatchDecider):
    """returns True if there are duplicates."""

    def check_valid(self) -> None:
        self.validate_zero_or_more_args(types=[Header])
        super().check_valid()

    def _decide_match(self, skip=None) -> None:
        name = self.first_non_term_qualifier(self.name)
        fingerprint, lines = FingerPrinter._capture_line(self, name, skip=skip)
        self.match = len(lines) > 1

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)


class DupLines(ValueProducer):
    """returns a list of duplicate lines seen so far."""

    def check_valid(self) -> None:
        self.validate_zero_or_more_args(types=[Header])
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        name = self.first_non_term_qualifier(self.name)
        fingerprint, lines = FingerPrinter._capture_line(self, name, skip=skip)
        lines = lines[:]
        pln = self.matcher.csvpath.line_monitor.physical_line_number
        lines.remove(pln)
        self.value = lines

    def _decide_match(self, skip=None) -> None:
        self.match = len(self.to_value(skip=skip)) > 0


class FingerPrinter:
    @classmethod
    def _capture_line(cls, mc, name: str, skip=None) -> tuple[str, list[int]]:
        values = mc.matcher.get_variable(name, set_if_none={})
        fingerprint = FingerPrinter._fingerprint(mc, skip=skip)
        if fingerprint not in values:
            values[fingerprint] = []
        pln = mc.matcher.csvpath.line_monitor.physical_line_number
        if pln not in values[fingerprint]:
            values[fingerprint].append(pln)
        mc.matcher.set_variable(name, value=values)
        return (fingerprint, values[fingerprint])

    @classmethod
    def _fingerprint(cls, mc, skip=None) -> str:
        if len(mc.children) == 1:
            if isinstance(mc.children[0], Equality):
                siblings = mc.children[0].commas_to_list()
                fingerprint = FingerPrinter._fingerprint_for_children(
                    siblings, skip=skip
                )
            elif isinstance(mc.children[0], Header):
                fingerprint = FingerPrinter._fingerprint_for_children(
                    [mc.children[0]], skip=skip
                )
        else:
            fingerprint = FingerPrinter._fingerprint_for_line(mc.matcher.line)
        return fingerprint

    @classmethod
    def _fingerprint_for_children(cls, sibs, skip=None) -> str:
        string = ""
        for _ in sibs:
            string += f"{_.to_value(skip=skip)}"
        return hashlib.sha256(string.encode("utf-8")).hexdigest()

    @classmethod
    def _fingerprint_for_line(cls, line) -> str:
        string = ""
        for _ in line:
            string += f"{_}"
        return hashlib.sha256(string.encode("utf-8")).hexdigest()
