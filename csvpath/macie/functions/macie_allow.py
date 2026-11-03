from typing import Any

from csvpath.matching.functions.function import Function
from csvpath.matching.functions.function_focus import SideEffect
from csvpath.matching.functions.args import Args
from csvpath.matching.productions import Term

from ..macie_exceptions import MacieException
from .macie_run import MacieRun


class MacieAllowRegex(SideEffect):
    """registers a regex allow list for the csvpath's Macie identifiers. An
    occurrence that fully matches the regex is not reported."""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Registers a Macie regex allow list. Every macie_cdi() and
                macie_mdi() in the csvpath skips an occurrence whose text
                fully matches the regex.

                Generated from a Macie allow list. It never contributes to
                matching.
            """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(name="allow list name", types=[Term], actuals=[str])
        a.arg(name="regex", types=[Term], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()
        #
        # registered before any line, so the order of the functions in the
        # csvpath doesn't matter
        #
        try:
            self._register()
        except (MacieException, ValueError, TypeError) as e:
            MacieRun.setup_failed(matcher=self.matcher, error=e)
            raise

    def _register(self) -> None:
        name, regex = (s.to_value() for s in self.siblings())
        if regex.startswith("/") and regex.endswith("/") and len(regex) > 1:
            regex = regex[1:-1]
        run = MacieRun.for_matcher(matcher=self.matcher)
        if name not in run.allow_lists.names:
            run.allow_lists.add_regex(name=name, pattern=regex)

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()


class MacieAllowWords(SideEffect):
    """registers a text allow list for the csvpath's Macie identifiers. An
    occurrence whose text equals an entry, ignoring case, is not reported.
    The entries come from load_list(), e.g.

        macie_allow_words.nocontrib("public-names", load_list("b8c2d4f6"))
    """

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Registers a Macie text allow list. Every macie_cdi() and
                macie_mdi() in the csvpath skips an occurrence whose text
                equals an entry, ignoring case.

                The first argument is the allow list's name. The second
                must be load_list(), which loads the entries once, before
                any line. In a named-paths group the list is in the group's
                assets, written when the Macie wrapper was loaded.

                Generated from a Macie allow list. It never contributes to
                matching.
            """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(name="allow list name", types=[Term], actuals=[str])
        a.arg(name="entries", types=[Function], actuals=[None, Any])
        self.args.validate(self.siblings())
        #
        # validates the children first, so load_list() has loaded its list
        #
        super().check_valid()
        try:
            self._register()
        except (MacieException, ValueError, TypeError) as e:
            MacieRun.setup_failed(matcher=self.matcher, error=e)
            raise

    def _register(self) -> None:
        name_term, entries = self.siblings()
        if entries.name != "load_list":
            raise MacieException(
                f"macie_allow_words() takes its entries from load_list(), not {entries.name}()"
            )
        name = name_term.to_value()
        values = entries.to_value()
        if not isinstance(values, (list, tuple)):
            raise MacieException(f"Allow list {name} entries must be a list")
        run = MacieRun.for_matcher(matcher=self.matcher)
        if name not in run.allow_lists.names:
            run.allow_lists.add_words(name=name, entries=list(values))

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()
