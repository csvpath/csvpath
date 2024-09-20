# pylint: disable=C0114
from csvpath.matching.productions import Header, Variable, Term
from ..function_focus import ValueProducer
from ..function import Function


class Put(ValueProducer):
    """Sets a variable with or without a tracking value"""

    def check_valid(self) -> None:
        self.validate_two_or_three_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        varname = None
        c1 = self._child_one()
        varname = c1.to_value(skip=skip)
        c2 = self._child_two()
        key = c2.to_value(skip=skip)
        value = None
        if len(self.children[0].children) > 2:
            value = self.children[0].children[2].to_value(skip=skip)
        else:
            value = key
            key = None
        self.matcher.set_variable(varname, value=value, tracking=key)
        self.value = self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip) is not None  # pragma: no cover
