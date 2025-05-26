# pylint: disable=C0114
import hashlib
from csvpath.util.hasher import Hasher
from csvpath.matching.util.exceptions import DataException
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import SideEffect
from ..function import Function
from ..args import Args


class LineFingerprint(SideEffect):
    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Sets the line-by-line SHA256 hash of the current data file into a variable.
                    You can use a name qualifier to name the variable. Otherwise, the name will be
                    by_line_fingerprint.

                    Since the hash is created line-by-line it changes on every scan. And even if
                    all lines are scanned the fingerprint at the end of the run is highly unlikely
                    to match the file fingerprint from the manifest.json. This difference is due to
                    the way lines are fed into the fingerprint algorithm, skipped blanks, and other
                    artifacts. Line fingerprint simply gives you an additional tool for ascertaining
                    the identity of certain input data bits.
            """
            ),
        ]
        self.name_qualifier = True
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
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Enters the SHA256 hash of the current data file into metadata.

                    A file's hash is available in run metadata. However, this function can
                    do a couple of things that may have value.

                    First, it can enter the data
                    into the meta.json file as a stand-alone value under any name you like.

                    Second and more importantly, it takes a fingerprint of a source-mode:preceding
                    run's data file. This allows you to easily confirm that the input to the
                    current csvpath was the exact output of the preceding csvpath and different
                    from the original data file.
            """
            ),
        ]
        self.name_qualifier = True
        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        n = self.first_non_term_qualifier("file_fingerprint")
        h = Hasher().hash(self.matcher.csvpath.scanner.filename, encode=False)
        self.matcher.csvpath.metadata[n] = h
        self.matcher.csvpath.metadata["hash_algorithm"] = "sha256"
        self.match = self.default_match()


class StoreFingerprint(SideEffect):
    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Migrates a by-line fingerprint from its variable into run metadata. If a name
                qualifier was used to create the by-line fingerprint the same name must be used
                with this function.
            """
            ),
        ]
        self.name_qualifier = True
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
