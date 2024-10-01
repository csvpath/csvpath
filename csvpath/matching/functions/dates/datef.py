# pylint: disable=C0114
import datetime
from ..function_focus import ValueProducer
from ..args import Args
from ..function import Function
from csvpath.matching.productions import Header, Variable, Reference, Term


class Date(ValueProducer):
    """parses a date from a string"""

    def check_valid(self) -> None:
        # self.validate_two_args()
        args = Args()
        a = args.argset(2)
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[str])
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[str])
        args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        eq = self.children[0]
        v = eq.left.to_value(skip=skip)
        v = f"{v}".strip()
        fmt = eq.right.to_value(skip=skip)
        fmt = f"{fmt}".strip()
        d = datetime.datetime.strptime(v, fmt)
        if not self.name == "datetime":
            d = d.date()
        self.value = d

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover
        # self.match = self._noop_match()  # pragma: no cover
