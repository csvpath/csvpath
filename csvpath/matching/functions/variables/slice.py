from typing import Any
from csvpath.matching.productions import Term, Variable, Header
from csvpath.matching.functions.function import Function
from ..function_focus import ValueProducer
from ..args import Args
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.expression_utility import ExpressionUtility as exut


class Slice(ValueProducer):
    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                Slice extracts part of a stack into a new stack.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(3)
        a.arg(
            name="stack var name",
            types=[Term],
            actuals=[str],
        )
        a.arg(
            name="from here",
            types=[Term, Variable, Header, Function],
            actuals=[int],
        )
        a.arg(
            name="to here",
            types=[None, Term, Variable, Header, Function],
            actuals=[int],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()
        varname = None
        c = self._child_one()
        if isinstance(c, Variable):
            varname = c.name
        else:
            varname = self._value_one(skip=skip)
        v = self.matcher.get_variable(varname)
        if v is None:
            msg = f"There is no variable {varname}"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
            return
        if not isinstance(v, (tuple, list)):
            msg = "Variable must be a stack"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
            return

        ffrom = self._value_two(skip=skip)
        to = self._value_three(skip=skip)
        print(f"from {ffrom} to {to}")
        if ffrom > to:
            msg = "Slice stop index is before start index"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
            return
        if ffrom < 0:
            msg = "Slice cannot start at a negative index"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
            return
        if to >= len(v):
            msg = "Slice cannot be longer than the source"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
            return
        t = v[ffrom : to + 1]
        self.value = t

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip) is not None  # pragma: no cover
        self.match = self.default_match()
