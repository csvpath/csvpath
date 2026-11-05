from ..function_focus import ValueProducer
from ..args import Args


class LineValuesStack(ValueProducer):
    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                Returns the current line values as a stack variable.
            """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.validate(self.siblings())
        super().check_valid()  # pragma: no cover

    def _produce_value(self, skip=None) -> None:
        if self.matcher.line:
            stack = self.matcher.line[:]
        else:
            stack = []
            self.matcher.csvpath.logger.debug("No line in matcher")
        self.value = stack

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()
