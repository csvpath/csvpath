# pylint: disable=C0114
from ..function_focus import ValueProducer
from ..args import Args


class PrintQueue(ValueProducer):
    """returns the number of lines printed to the Printer instances"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        if not self.matcher.csvpath.printers or len(self.matcher.csvpath.printers) == 0:
            self.value = 0
        else:
            self.value = self.matcher.csvpath.printers[0].lines_printed

    def _decide_match(self, skip=None) -> None:  # pragma: no cover
        self.match = self.default_match()
