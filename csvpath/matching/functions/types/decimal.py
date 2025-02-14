# pylint: disable=C0114
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import ChildrenException, MatchException
from csvpath.matching.productions import Header, Variable, Reference, Term
from csvpath.matching.functions.function import Function
from .nonef import Nonef
from ..function_focus import ValueProducer
from ..args import Args
from .type import Type


class Decimal(Type):
    def check_valid(self) -> None:
        self.match_qualifiers.append("notnone")
        self.value_qualifiers.append("notnone")
        self.match_qualifiers.append("strict")
        self.value_qualifiers.append("strict")
        self.description = [
            self._cap_name(),
            f"{self.name}() is a type function often used as an argument to line().",
            f"It indicates that the value it receives must be {self._a_an()} {self.name}.",
        ]
        #
        #
        #
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
            # Matcher via Type will take care of mismatches and Nones. Args handles nonnone
            #
            if self.notnone is True:
                self.match = False
                return
            self.match = True
            return
        if self.name == "decimal":
            #
            # we know this value is a number because Args checked it.
            # but would a user know from looking at it that it was a float?
            # if strict, we require the fractional part. if not strict any
            # whole number can be a decimal with an unwritten .0 so we
            # allow it.
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
                    self.match = False
                    return
            self.match = True
        else:
            if f"{h}".find(".") > -1:
                msg = "Integers cannot have a fractional part"
                if self.has_qualifier("strict"):
                    self.matcher.csvpath.error_manager.handle_error(
                        source=self, msg=msg
                    )
                    if self.matcher.csvpath.do_i_raise():
                        raise MatchException(msg)
                    self.match = False
                    return
                i = ExpressionUtility.to_int(h)
                f = ExpressionUtility.to_float(h)
                if i == f:
                    # the fractional part is 0, so we'll allow it
                    self.match = True
                else:
                    self.matcher.csvpath.error_manager.handle_error(
                        source=self, msg=msg
                    )
                    if self.matcher.csvpath.do_i_raise():
                        raise MatchException(msg)
                    self.match = False
                    return
            self.match = True
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
