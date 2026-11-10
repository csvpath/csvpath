# pylint: disable=C0114
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args


class Concat(ValueProducer):
    """concats two strings"""

    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
               Concatenates any number of strings, numbers, or bool values. Alternatively, pass
               a stack variable to stringify its items.
        """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(
            name="value",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, int, float, bool, self.args.EMPTY_STRING],
        )
        a.arg(
            name="append this",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, int, float, bool, list, self.args.EMPTY_STRING],
        )
        a = self.args.argset(2)
        a.arg(
            name="join these",
            types=[Variable, Function],
            actuals=[list, tuple],
        )
        a.arg(name="delimiter", types=[None, Term], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        siblings = self.siblings()
        s = siblings[0].to_value(skip=skip)
        if len(siblings) <= 2 and isinstance(s, (list, tuple)):
            d = ","
            if len(siblings) == 2:
                d = str(siblings[1].to_value(skip=skip))
            self.value = d.join(s)
        else:
            v = ""
            for s in siblings:
                c = s.to_value(skip=skip)
                if isinstance(c, list):
                    c = [str(c) for c in c]
                    c = "".join(c)
                v = f"{v}{c}"
            self.value = v
            print(f"csvcat: {self.value}")

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()
