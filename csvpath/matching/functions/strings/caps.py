# pylint: disable=C0114
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args


class Capitalize(ValueProducer):
    """uppercases the first character of a string or words"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[str])
        a.arg(
            name="if true, init-cap all words",
            types=[None, Term, Function, Variable],
            actuals=[bool],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        v = self._value_one(skip=skip)
        v = v.strip() if v else ""
        v2 = self._value_two(skip=skip)
        v3 = None
        if v2:
            ws = []
            for w in v.split(" "):
                w = w[0].upper() + w[1:]
                ws.append(w)
            v3 = " ".join(ws)
        else:
            v3 = v[0].upper() + v[1:]
        self.value = v3

    def _decide_match(self, skip=None) -> None:
        v = self.to_value(skip=skip)
        self.match = v is not None
