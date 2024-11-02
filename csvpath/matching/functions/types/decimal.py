# pylint: disable=C0114
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.productions import Term
from ..function import Function
from .nonef import Nonef
from ..function_focus import ValueProducer
from ..args import Args
from .type import Type


class Decimal(ValueProducer, Type):
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
                msg = self.decorate_error_message(
                    f"Incorrect argument: {s} is not allowed"
                )
                self.parent.raise_if(ChildrenException(msg))
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        h = self.resolve_value()
        if h is None:
            #
            # Matcher via Type will take care of mismatches and Nones
            #
            if self.notnone is True:
                self.match = False
                msg = self.decorate_error_message(
                    f"'{self._value_one(skip=skip)}' cannot be empty"
                )
                self.parent.raise_if(ChildrenException(msg))
                return
            else:
                self.match = True
                return
        if self.name == "decimal":
            #
            # we know this value is a number because Args checked it.
            # but would a user know from looking at it that it was a float?
            #
            if self.has_qualifier("strict"):
                if f"{h}".strip().find(".") == -1:
                    self.match = False
                    n = self._value_one()
                    msg = self.decorate_error_message(
                        f"'{n}' has 'strict' but value does not have a '.'"
                    )
                    self.parent.raise_if(ChildrenException(msg))
                    return
                else:
                    self.match = True
            elif self.has_qualifier("weak"):
                self.match = True
            elif f"{h}".strip().find(".") == -1:
                self.match = False
                return
            else:
                self.match = True
        else:
            if f"{h}".find(".") > -1:
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
