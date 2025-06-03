# pylint: disable=C0114
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.productions import Term
from ..function_focus import ValueProducer
from ..args import Args


class Percent(ValueProducer):
    """return the percent scanned, matched or data lines seen of
    the count of total data lines"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                   Returns the percent of scanned, matched or all lines so-far seen of
                   the total data lines in the file. Data lines have data. The total
                   does not include blanks.

                   By default percent() tracks % matches of total lines in the file. If
                   percent() has the onmatch qualifier it always tracks matches, overriding
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(name="scan, match, or line", types=[Term], actuals=[str])
        self.args.validate(self.siblings_or_equality())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        which = self.children[0].to_value(skip=skip)
        if which is None or self.onmatch:
            if which and which != "match" and self.onmatch:
                msg = "percent() has the onmatch qualifier but its argument is not 'match'"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise ChildrenException(msg)
            which = "match"

        if which not in ["scan", "match", "line"]:
            # correct structure / children exception. we could probably do this
            # in check_validate since we're requiring a Term, but this is fine.
            msg = "percent() argument must be scan, match, or line"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise ChildrenException(msg)

        if which == "line":
            count = self.matcher.csvpath.line_monitor.data_line_count
        elif which == "scan":
            count = self.matcher.csvpath.current_scan_count  # pragma: no cover
        else:
            count = self.matcher.csvpath.current_match_count

        total = self.matcher.csvpath.line_monitor.data_end_line_count
        value = 0
        if total > 0:
            value = count / total
        self.value = round(value, 2)
        self.matcher.csvpath.logger.debug(
            f"Percent: val: {value}, cnt: {count}, total: {total}, rounded: {self.value}"  # pylint: disable=C0301
        )

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()
