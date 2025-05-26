# pylint: disable=C0114
from ..function_focus import ValueProducer
from ..args import Args


class CountLines(ValueProducer):
    """the count (1-based of the number of data lines, blanks excluded"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    the count (1-based of the number of data lines seen, blanks excluded.

                    count_lines() is similar to line_number(). The difference is that
                    line_number() is 0-based and includes blank lines.
            """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matcher.csvpath.line_monitor.data_line_count


class LineNumber(ValueProducer):
    """the physical line number of the current line"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    The 0-based number of data lines seen, blanks excluded. This is also
                    known as the physical line number.

                    count_lines() is similar but is 1-based and excludes blank lines.
            """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matcher.csvpath.line_monitor.physical_line_number
