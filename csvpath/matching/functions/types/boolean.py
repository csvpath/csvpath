# pylint: disable=C0114
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.productions import Term, Variable, Header
from ..function import Function, CheckedUnset
from ..function_focus import ValueProducer
from ..args import Args
from .type import Type


class Boolean(ValueProducer, Type):
    def check_valid(self) -> None:
        self.value_qualifiers.append("notnone")
        self.match_qualifiers.append("distinct")
        self.description = [
            self._cap_name(),
            self.wrap(
                f"{self.name}() is a line() schema type representing a bool value."
            ),
            self.wrap("To generate a particular bool value use yes() or no()."),
            self.wrap(
                """As you would think, setting distinct limits the number of lines to
            four, for practical purposes. Namely: yes(), no(), none(), and a header name."""
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="value",
            types=[Term, Variable, Header, Function],
            actuals=[None, bool, str],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _decide_match(self, skip=None) -> None:
        # we need to make sure a value is produced so that we see
        # any errors. when we stand alone we're just checking our
        # boolean-iness. when we're producing a value we're checking
        # boolean-iness and casting and raising errors.
        v = self.to_value(skip=skip)
        self.match = v in [True, False]  # pragma: no cover

    def _produce_value(self, skip=None) -> None:
        c = self._child_one()
        v = None
        if isinstance(c, Term):
            v = self.matcher.get_header_value(c.value)
        else:
            v = c.to_value(skip=skip)
        if v is None or f"{v}".strip() == "":
            self.value = CheckedUnset()
            if self.notnone is True:
                msg = "Value cannot be empty because notnone is set"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
        else:
            ret = self._do_i_match(value=v, skip=skip)
            if ret[0] is True:
                self.value = True
            else:
                self.value = CheckedUnset()
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=ret[1])
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(ret[1])
                self.value = False

    def _do_i_match(self, *, value=None, skip=None) -> tuple[bool, str | None]:
        t = Boolean._is_match(value=value, strict=self.strict)
        if t[0]:
            self._distinct_if(skip=skip, value=value)
        return t

    @classmethod
    def _is_match(cls, value=None, strict=False) -> tuple[bool, str | None]:
        b = None
        if strict:
            #
            # checks: True, False, true, false
            # to_simple_bool doesn't convert: 1, 0, None.
            # to include those we would need to use to_bool().
            # neither checks "on", "off", "yes", "no".
            # "" has already been checked above.
            #
            b = ExpressionUtility.to_simple_bool(value)
        else:
            b = ExpressionUtility.to_bool(value)
        if b in [True, False]:
            return (True, None)
        return (False, f"{value} is not a boolean value")
