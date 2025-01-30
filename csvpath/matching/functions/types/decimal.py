# pylint: disable=C0114
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import ChildrenException, MatchException
from csvpath.matching.productions import Header, Variable, Reference, Term
from csvpath.matching.functions.function import Function
from .nonef import Nonef
from ..function_focus import ValueProducer
from ..args import Args
from .type import Type


class Decimal(ValueProducer, Type):
    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(3)
        a.arg(
            name="header",
            types=[Header, Variable, Function, Reference],
            actuals=[None, str, int],
        )
        a.arg(
            name="max",
            types=[None, Term, Function, Variable],
            actuals=[None, float, int],
        )
        a.arg(
            name="min",
            types=[None, Term, Function, Variable],
            actuals=[None, float, int],
        )
        self.args.validate(self.siblings())
        for i, s in enumerate(self.siblings()):
            if isinstance(s, Function) and not isinstance(s, Nonef):
                self.match = False
                msg = f"Incorrect argument: {s} is not allowed"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        h = self._value_one(skip=skip)
        if h is None:
            #
            # Matcher via Type will take care of mismatches and Nones
            #
            if self.notnone is True:
                self.match = False
                #
                # should be caught by Args
                #
                """ """
                msg = f"'{self._value_one(skip=skip)}' cannot be empty"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
                """ """
                return
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
                    msg = f"'{n}' has 'strict' but value does not have a '.'"
                    self.matcher.csvpath.error_manager.handle_error(
                        source=self, msg=msg
                    )
                    if self.matcher.csvpath.do_i_raise():
                        raise MatchException(msg)
                    return
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
        self._val_in_bounds(val, skip=skip)

    def _val_in_bounds(self, val, skip=None) -> None:
        # find max
        dmax = self._value_two(skip=skip)
        if dmax is not None:
            dmax = self._to(dmax)
        # find min
        dmin = self._value_three(skip=skip)
        if dmin is not None:
            dmin = self._to(dmin)
        # get result

        if (dmax is None or val <= dmax) and (dmin is None or val >= dmin):
            self.match = True
        else:
            self.match = False

    def _to(self, n):
        if self.name == "decimal":
            f = ExpressionUtility.to_float(n)
            if not isinstance(f, float):
                msg = f"Cannot convert {n} to float"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
            return f
        if self.name == "integer":
            i = ExpressionUtility.to_int(n)
            if not isinstance(i, int):
                msg = f"Cannot convert {n} to int"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
            return i
        #
        #
        #
        msg = f"Unknown name: {self.name}"
        self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
        if self.matcher.csvpath.do_i_raise():
            raise MatchException(msg)
        return None
