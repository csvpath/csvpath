# pylint: disable=C0114
from ..function_focus import ValueProducer
from ..args import Args


class CountScans(ValueProducer):
    """the current number of lines scanned"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Returns the current number of lines that have been scanned.

                    Scanning predicts a specific number of lines for a given file. However,
                    if a line is expected to be scanned but is skipped because it is blank
                    it is not counted as scanned.

                    For example, a scanning instruction [1-3] indicates that lines 1, 2, and 3 would
                    be scanned. But if line 2 is blank and we are configured to skip blank lines (the
                    default), when we're done scanning we will have a count_scans() total of 2, not 3, because
                    we skipped a blank line.
            """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matcher.csvpath.current_scan_count
