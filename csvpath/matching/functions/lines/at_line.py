# pylint: disable=C0114
from csvpath.matching.productions import Term
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import MatchDecider
from ..function import Function
from ..args import Args


class AtLine(MatchDecider):
    def check_valid(self) -> None:
        self.description = []
        if self.name == "at_line":
            self.description.append(
                self.wrap(
                    "True if the current line is the argument or among the arguments of this function."
                )
            )
        elif self.name == "not_line":
            self.description.append(
                self.wrap(
                    "True if the current line is not the argument or among the arguments of this function."
                )
            )
        else:
            # this shouldn't happen. if it did it would be a FunctionFactory bug
            raise ChildrenException(f"Unknown function name: {self.name}")

        self.args = Args(matchable=self)
        self.args.argset(1).arg(name="this line", types=[Function, Term], actuals=[int])
        self.args.argset().arg(name="a line", types=[Function, Term], actuals=[int])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        lines = None
        try:
            lines = self.lines
        except Exception:
            sibs = self.siblings()
            self.lines = [s.to_value(skip=skip) for s in sibs]
            lines = self.lines
        if self.matcher.csvpath.line_monitor.data_line_number in lines:
            if self.name == "at_line":
                self.match = True
            else:
                self.match = False
        else:
            if self.name == "at_line":
                self.match = False
            else:
                self.match = True
