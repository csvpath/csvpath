# pylint: disable=C0114
from ..function_focus import ValueProducer
from ..args import Args


class CountHeaders(ValueProducer):
    """returns the current number of headers expected or
    the actual number of headers in a given line"""

    def check_valid(self) -> None:
        if self.name == "count_headers":
            self.description = [
                self._cap_name(),
                self.wrap(
                    """\
                        count_headers() returns the number of headers currently in-effect. It
                        is our expected number, not the number of values we actually get.

                        Keep in mind that the number of headers in a file can change at any
                        time. Each time we call reset_headers() the return from count_headers()
                        is also reset.
                """
                ),
            ]
        elif self.name == "count_headers_in_line":
            self.description = [
                self._cap_name(),
                self.wrap(
                    """\
                        count_headers_in_line() returns the number of headers in the current line.
                """
                ),
            ]

        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        if self.name == "count_headers":
            ret = len(self.matcher.csvpath.headers)
            self.value = ret
        elif self.name == "count_headers_in_line":
            self.value = len(self.matcher.line)
