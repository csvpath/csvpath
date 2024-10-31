# pylint: disable=C0114
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.productions import Term
from ..function_focus import ValueProducer
from ..args import Args


class Percent(ValueProducer):
    """return the percent scanned, matched or data lines seen of
    the count of total data lines"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(types=[Term], actuals=[str])
        self.args.validate(self.siblings_or_equality())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        which = self.children[0].to_value(skip=skip)
        if which not in ["scan", "match", "line"]:
            # correct structure / children exception. we could probably do this
            # in check_validate since we're requiring a Term, but this is fine.
            self.raiseChildrenException(
                "percent() argument must be scan, match, or line"
            )  # pragma: no cover
        if which == "line":
            count = self.matcher.csvpath.line_monitor.data_line_count
        elif which == "scan":
            count = self.matcher.csvpath.current_scan_count  # pragma: no cover
        else:
            count = self.matcher.csvpath.current_match_count
        total = self.matcher.csvpath.line_monitor.data_end_line_count
        value = count / total
        self.value = round(value, 2)
        self.matcher.csvpath.logger.debug(
            f"Percent: val: {value}, cnt: {count}, total: {total}, rounded: {self.value}"  # pylint: disable=C0301
        )

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()
