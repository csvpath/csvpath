# pylint: disable=C0114
from ..function_focus import ValueProducer
from ..args import Args


class CountBytes(ValueProducer):
    """returns the total data bytes written count. CsvPath instances
    do not write out data, so this value would be 0 for them."""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Returns the total data bytes written count.

                    This function is only for named-path group runs. Individual CsvPath
                    instances do not write out data, so this value would be 0 for them.
            """
            ),
        ]

        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matcher.csvpath.lines.bytes_written()
