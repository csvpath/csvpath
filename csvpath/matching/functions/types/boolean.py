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
        self.description = [
            self._cap_name(),
            f"{self.name}() is a line() schema type representing a bool value.",
            "To generate a particular bool value use yes() or no().",
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

    def _produce_value(self, skip=None) -> None:
        c = self._child_one()
        v = None
        if isinstance(c, Term):
            v = self.matcher.get_header_value(self, c.value)
        else:
            v = c.to_value(skip=skip)
        if v is None or f"{v}".strip() == "":
            self.value = CheckedUnset()
            #
            # pretty sure this none should be caught by the args validation
            #
            if self.notnone is True:
                msg = "Value cannot be empty because notnone is set"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
        else:
            v = ExpressionUtility.to_bool(v)
            if v in [True, False]:
                self.value = v
            else:
                self.value = CheckedUnset()
                #
                # pretty sure this none should also be caught by Args
                #
                msg = f"Not a boolean value in {self.my_chain}: '{v}'"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)

    def _decide_match(self, skip=None) -> None:
        # we need to make sure a value is produced so that we see
        # any errors. when we stand alone we're just checking our
        # boolean-iness. when we're producing a value we're checking
        # boolean-iness and casting and raising errors.
        v = self.to_value(skip=skip)
        self.match = v in [True, False]  # pragma: no cover
