from typing import Any
from csvpath.matching.productions import Term, Variable
from ..function_focus import SideEffect
from ..args import Args


class Clear(SideEffect):
    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Clears a variable by removing it.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="var name",
            types=[Term],
            actuals=[str],
        )
        a = self.args.argset(1)
        a.arg(
            name="var",
            types=[Variable],
            actuals=[None, Any],
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
        self.matcher.clear_variable(varname)
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip) is not None  # pragma: no cover
        self.match = self.default_match()
