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

        dmax = self._value_two(skip=skip)
        if dmax is not None:
            dmax = self._to(name=self.name, n=dmax)
        dmin = self._value_three(skip=skip)
        if dmin is not None:
            dmin = self._to(name=self.name, n=dmin)

        ret = self._is_match(
            name=self.name,
            value=h,
            dmax=dmax,
            dmin=dmin,
            strict=self.has_qualifier("strict"),
        )
        if ret[0] is False:
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=ret[1])
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(ret[1])
            self.match = False
            return
        self.match = True

    def _is_match(
        self,
        *,
        name: str,
        value: str,
        dmax: int | float,
        dmin: int | float,
        strict: str,
    ) -> tuple[bool, str | None]:
        ret = self._dot(name=self.name, h=value, strict=self.has_qualifier("strict"))
        if ret[0] is False:
            return ret
        val = self._to(name=self.name, n=value)
        if isinstance(val, str):
            return (False, val)
        m = self._val_in_bounds(val=val, dmax=dmax, dmin=dmin)
        if m is False:
            return (False, "Value is out of bounds")
        return (True, None)

    def _dot(self, *, name: str, h: str, strict: bool) -> tuple[bool, str | None]:
        if self.name == "decimal":
            if strict:
                if f"{h}".strip().find(".") == -1:
                    msg = f"'{h}' has 'strict' but value does not have a '.'"
                    return (False, msg)
            return (True, None)
        else:
            if f"{h}".find(".") > -1:
                msg = "Integers cannot have a fractional part"
                if strict:
                    return (False, msg)
                i = ExpressionUtility.to_int(h)
                f = ExpressionUtility.to_float(h)
                if i == f:
                    # the fractional part is 0, so we'll allow it
                    return (True, None)
                else:
                    return (False, msg)

    def _val_in_bounds(self, *, val, dmax, dmin) -> None:
        return (dmax is None or val <= dmax) and (dmin is None or val >= dmin)

    def _to(self, *, name: str, n: str):
        if self.name == "decimal":
            f = ExpressionUtility.to_float(n)
            if not isinstance(f, float):
                return f"Cannot convert {n} to float"
            return f
        if self.name == "integer":
            i = ExpressionUtility.to_int(n)
            if not isinstance(i, int):
                return f"Cannot convert {n} to int"
            return i
