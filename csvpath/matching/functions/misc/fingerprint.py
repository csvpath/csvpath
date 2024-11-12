# pylint: disable=C0114
import hashlib
from csvpath.matching.util.exceptions import DataException
from ..function_focus import SideEffect
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function import Function
from ..args import Args


class LineFingerprint(SideEffect):
    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        m = self.matcher.get_variable(
            self.first_non_term_qualifier("by_line_fingerprint")
        )
        if m is None:
            m = hashlib.sha256()
            self.matcher.set_variable(
                self.first_non_term_qualifier("by_line_fingerprint"), value=m
            )
        m.update(f"{self.matcher.line}".encode("utf-8"))
        self.match = self.default_match()


class FileFingerprint(SideEffect):
    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        n = self.first_non_term_qualifier("file_fingerprint")
        with open(self.matcher.csvpath.scanner.filename, "rb") as f:
            h = hashlib.file_digest(f, hashlib.sha256)
            self.matcher.csvpath.metadata[n] = h.hexdigest()
            self.matcher.csvpath.metadata["hash_algorithm"] = "sha256"
        self.match = self.default_match()


class StoreFingerprint(SideEffect):
    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        f = self.first_non_term_qualifier("by_line_fingerprint")
        m = self.matcher.get_variable(f)
        if m is None:
            m = hashlib.sha256()
        h = m.hexdigest()
        self.matcher.csvpath.metadata[f] = h
        self.matcher.csvpath.metadata["hash_algorithm"] = "sha256"
        del self.matcher.csvpath.variables[f]
        self.match = self.default_match()
