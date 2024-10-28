# pylint: disable=C0114
import datetime
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header
from csvpath.matching.functions.function import Function
from csvpath.matching.util.exceptions import ChildrenException
from ..args import Args


class Now(ValueProducer):
    """returns the current datetime"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.argset(0)
        if self.name in ["thisyear", "thismonth", "today"]:
            self.args.validate(self.siblings())
        else:
            self.args.argset(1).arg(
                types=[None, Term, Function, Header, Variable], actuals=[None, str]
            )
            self.args.validate(self.siblings())
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
