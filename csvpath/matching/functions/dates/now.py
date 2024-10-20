# pylint: disable=C0114
import datetime
from ..function_focus import ValueProducer
from csvpath.matching.productions.term import Term
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.header import Header
from csvpath.matching.functions.function import Function
from csvpath.matching.util.exceptions import ChildrenException
from ..args import Args


class Now(ValueProducer):
    """returns the current datetime"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.argset(1).arg(
            types=[None, Term, Function, Header, Variable], actuals=[str]
        )
        self.args.validate(self.siblings())
        if self.name in ["thisyear", "thismonth", "today"]:
            if len(self.children) > 0:
                raise ChildrenException(f"Function {self.name} cannot have arguments")
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        form = None
        if len(self.children) == 1:
            form = self.children[0].to_value(skip=skip)
            form = f"{form}".strip()
        elif self.name == "thisyear":
            form = "%Y"
        elif self.name == "thismonth":
            form = "%m"
        elif self.name == "today":
            form = "%d"
        x = datetime.datetime.now()
        xs = None
        if form:
            xs = x.strftime(form)
        else:
            xs = f"{x}"
        self.value = xs

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover
