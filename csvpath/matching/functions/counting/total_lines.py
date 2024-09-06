# pylint: disable=C0114
from ..function_focus import ValueProducer


class TotalLines(ValueProducer):
    """returns the total data lines count for the file (1-based"""

    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matcher.csvpath.line_monitor.data_end_line_count