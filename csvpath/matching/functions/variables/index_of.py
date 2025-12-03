from typing import Any
from csvpath.matching.productions import Header, Variable, Term, Reference
from csvpath.matching.util.exceptions import MatchException
from ..function_focus import ValueProducer
from ..function import Function
from ..args import Args


class IndexOf(ValueProducer):
    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Finds the position of a value within a stack, if present.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="stack name",
            types=[Term],
            actuals=[str],
        )
        a.arg(
            name="value",
            types=[Header, Term, Function, Variable, Reference],
            actuals=[Any, Args.EMPTY_STRING],
        )
        a = self.args.argset(2)
        a.arg(
            name="stack",
            types=[Variable],
            actuals=[list, tuple],
        )
        a.arg(
            name="value",
            types=[Header, Term, Function, Variable, Reference],
            actuals=[Any, Args.EMPTY_STRING],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        varname = None
        c = self._child_one()
        if isinstance(c, Variable):
            varname = c.name
        else:
            varname = self._value_one(skip=skip)
        v = self._value_two(skip=skip)
        s = self.matcher.get_variable(f"{varname}", set_if_none=[])
        if isinstance(s, (list, tuple)):
            try:
                self.value = s.index(v)
            except ValueError:
                self.value = -1
        else:
            msg = f"Variable {varname} must be a stack variable"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip) is not None  # pragma: no cover
