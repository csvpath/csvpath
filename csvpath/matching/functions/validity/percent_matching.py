# pylint: disable=C0114
import hashlib
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import ValueProducer
from ..args import Args


class PercentMatching(ValueProducer):
    def check_valid(self) -> None:
        self.name_qualifier = False
        self.description = [
            self.wrap(
                """\
                    Returns the running percent of lines that match, using the
                    count of data lines scanned in the denominator.
            """
            )
        ]
        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.validate(self.siblings())
        super().check_valid()

    def _decide_match(self, skip=None) -> None:
        self.match == self.default_match()

    def _produce_value(self, skip=None) -> None:
        try:
            i = self.matcher.csvpath.current_match_count
            j = (
                1
                if self.matcher.csvpath.line_monitor.data_line_count == 0
                else self.matcher.csvpath.line_monitor.data_line_count
            )
            pm = 0
            if j > 0:
                pm = i / j
            pm = pm * 100
            self.value = pm
        except Exception as e:
            print(f"e: {e}")
