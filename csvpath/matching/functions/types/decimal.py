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
        if h is None or (isinstance(h, str) and h.strip() == ""):
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

        ret = Decimal._is_match(
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

    @classmethod
    def _is_match(
        cls,
        *,
        name: str,
        value: str,
        strict: bool,
        dmax: int | float = None,
        dmin: int | float = None,
    ) -> tuple[bool, str | None]:
        if value is False or value is None or value.strip() == "":
            return (False, "Value is not a number")
        ret = cls._dot(name=name, h=value, strict=strict)
        if ret[0] is False:
            return ret
        val = cls._to(name=name, n=value)
        if isinstance(val, str):
            return (False, val)
        m = cls._val_in_bounds(val=val, dmax=dmax, dmin=dmin)
        if m is False:
            return (False, "Value is out of bounds")
        return (True, None)

    @classmethod
    def _dot(cls, *, name: str, h: str, strict: bool) -> tuple[bool, str | None]:
        if name == "decimal":
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
                if i == f and i != h:
                    # the fractional part is 0, so we'll allow it
                    return (True, None)
                else:
                    return (False, msg)
        return (True, None)

    @classmethod
    def _val_in_bounds(cls, *, val, dmax, dmin) -> None:
        return (dmax is None or val <= dmax) and (dmin is None or val >= dmin)

    @classmethod
    def _to(cls, *, name: str, n: str):
        if name == "decimal":
            f = ExpressionUtility.to_float(n)
            if not isinstance(f, float):
                return f"Cannot convert {n} to float"
            return f
        if name == "integer":
            i = ExpressionUtility.to_int(n)
            if not isinstance(i, int):
                return f"Cannot convert {n} to int"
            return i
