# pylint: disable=C0114
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import ValueProducer


class Percent(ValueProducer):
    """return the percent scanned, matched or data lines seen of
    the count of total data lines"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        which = self.children[0].to_value(skip=skip)
        if which not in ["scan", "match", "line"]:
            raise ChildrenException(
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
        self.match = self._apply_default_match()
