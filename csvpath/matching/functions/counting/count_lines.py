# pylint: disable=C0114
from ..function_focus import ValueProducer


class CountLines(ValueProducer):
    """the count (1-based of the number of data lines, blanks excluded"""

    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matcher.csvpath.line_monitor.data_line_count


class LineNumber(ValueProducer):
    """the physical line number of the current line"""

    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matcher.csvpath.line_monitor.physical_line_number
