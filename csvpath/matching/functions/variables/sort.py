from typing import Any
from csvpath.matching.productions import Term, Variable
from ..function_focus import SideEffect
from ..args import Args
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.expression_utility import ExpressionUtility as exut


class Sort(SideEffect):
    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                Sorts a stack variable. If the second var evaluates to
                True or "desc" it is a descending sort.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="stack var name",
            types=[Term],
            actuals=[str],
        )
        a.arg(
            name="'desc' or True for descending",
            types=[None, Term],
            actuals=[None, bool, str],
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
            return
        if not isinstance(v, (tuple, list)):
            msg = "Variable must be a stack"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
            return
        s = self._value_two(skip=skip)
        s = exut.to_bool(s)
        if s is isinstance(s, bool):
            ...
        elif str(s).strip() == "desc":
            s = True
        else:
            s = False
        v.sort(reverse=s)

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip) is not None  # pragma: no cover
        self.match = self.default_match()
