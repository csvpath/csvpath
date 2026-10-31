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
