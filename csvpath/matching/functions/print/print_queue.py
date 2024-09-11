# pylint: disable=C0114
from ..function_focus import ValueProducer


class PrintQueue(ValueProducer):
    """returns the number of lines printed to the Printer instances"""

    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        if not self.matcher.csvpath.printers or len(self.matcher.csvpath.printers) == 0:
            self.value = 0
        else:
            self.value = self.matcher.csvpath.printers[0].lines_printed

    def _decide_match(self, skip=None) -> None:  # pragma: no cover
        self.match = self._noop_match()
