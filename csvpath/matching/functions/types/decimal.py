# pylint: disable=C0114
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.productions import Term
from ..function import Function
from .nonef import Nonef
from ..function_focus import ValueProducer
from ..args import Args


class Decimal(ValueProducer):
    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(5)
        a.arg(name="header name", types=[Term], actuals=[str, int])
        a.arg(name="max", types=[None, Term, Function], actuals=[None, float, int])
        a.arg(name="min", types=[None, Term, Function], actuals=[None, float, int])
        self.args.validate(self.siblings())
        for s in self.siblings():
            if isinstance(s, Function) and not isinstance(s, Nonef):
                self.match = False
                self.parent.raise_if(
                    ChildrenException(f"Incorrect argument: {s} is not allowed")
                )
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        val = self._value_one(skip=skip)
        h = None
        try:
            h = self.matcher.get_header_value(val)
            if h is None or f"{h}".strip() == "":
                self.value = None
                if self.notnone is True:
                    self.match = False
                    # pln = self.matcher.csvpath.line_monitor.physical_line_number
                    self.parent.raise_if(ChildrenException(f"'{val}' cannot be empty"))
        except (TypeError, IndexError) as e:
            self.match = False
            # pln = self.matcher.csvpath.line_monitor.physical_line_number
            self.parent.raise_if(
                ChildrenException(
                    f"Argument '{val}' does not identify a valid header value on this line"
                ),
                cause=e,
            )
            return
        #
        # we know this value can be a float because Args checked it.
        # but would a user know from looking at it that it was a float?
        #
        if self.name == "decimal":
            if self.has_qualifier("strict"):
                if h.find(".") == -1:
                    self.match = False
                    # pln = self.matcher.csvpath.line_monitor.physical_line_number
                    self.parent.raise_if(
                        ChildrenException(
                            f"Argument '{val}' has 'strict' but value does not have a '.'"
                        )
                    )
                    return
        else:
            if h.find(".") > -1:
                self.match = False
                return
        #
        # validate min and max
        #
        val = self._to(h)
        dmax = self._value_two(skip=skip)
        if dmax is not None:
            dmax = self._to(dmax)

        dmin = self._value_three(skip=skip)
        if dmin is not None:
            dmin = self._to(dmin)
        if (dmax is None or val <= dmax) and (dmin is None or val >= dmin):
            self.match = True
        else:
            self.match = False

    def _to(self, n):
        if self.name == "decimal":
            return ExpressionUtility.to_float(n)
        elif self.name == "integer":
            return ExpressionUtility.to_int(n)
