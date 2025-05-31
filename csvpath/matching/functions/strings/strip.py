# pylint: disable=C0114
from ..function_focus import ValueProducer
from csvpath.matching.productions import Variable, Header, Reference
from ..function import Function
from ..args import Args


class Strip(ValueProducer):
    """removes whitespace from the beginning and end of a string"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                   Alters a string by trimming leading and trailing whitespace.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="trim this",
            types=[Variable, Header, Reference, Function],
            actuals=[str],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        v = self.children[0].to_value()
        string = f"{v}"
        self.value = string.strip()

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)  # pragma: no cover
        self.match = self.default_match()  # pragma: no cover
