# pylint: disable=C0114
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.productions import Term, Variable, Header
from ..function import Function, CheckedUnset
from ..function_focus import ValueProducer
from ..args import Args


class Boolean(ValueProducer):
    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(types=[Term, Variable, Header, Function], actuals=[None, bool, str])
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
            # self.value = None
            if self.notnone is True:
                msg = self.decorate_error_message("Value cannot be empty")
                self.parent.raise_if(ChildrenException(msg))
        else:
            v = ExpressionUtility.to_bool(v)
            if v in [True, False]:
                self.value = v
            else:
                self.value = CheckedUnset()
                msg = self.decorate_error_message(f"Not a boolean value: '{v}'")
                self.parent.raise_if(ChildrenException(msg))

    def _decide_match(self, skip=None) -> None:
        # we need to make sure a value is produced so that we see
        # any errors. when we stand alone we're just checking our
        # boolean-iness. when we're producing a value we're checking
        # boolean-iness and casting and raising errors.
        v = self.to_value(skip=skip)
        self.match = v in [True, False]  # pragma: no cover
