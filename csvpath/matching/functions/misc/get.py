# pylint: disable=C0114
from csvpath.matching.productions import Header, Variable, Term
from ..function_focus import ValueProducer
from ..function import Function


class Get(ValueProducer):
    """returns a variable value, tracking value or stack index"""

    def check_valid(self) -> None:
        self.validate_one_or_two_args(
            one=[Header, Term, Function],
            left=[Header, Term, Function, Variable],
            right=[Header, Term, Function, Variable],
        )
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        varname = None
        c1 = self._child_one()
        if isinstance(c1, Variable):
            varname = c1.name
        else:
            varname = self._value_one(skip=skip)
        c2 = self._child_two()
        v = self.matcher.get_variable(varname)
        if v is None:
            self.value = None
        elif c2 is None:
            self.value = v
        else:
            t = self._value_two(skip=skip)
            if isinstance(t, int) and isinstance(v, list):
                self.value = v[t] if -1 < t < len(v) else None
            elif isinstance(v, dict) and t in v:
                self.value = v[t]
            else:
                self.value = None
                self.matcher.csvpath.logger.warning(
                    f"No way to provide {varname}.{t} given the available variables"
                )

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip) is not None  # pragma: no cover
