# pylint: disable=C0114
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import ValueProducer


class Sum(ValueProducer):
    """returns the running sum of numbers"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        var = self.first_non_term_qualifier(self.name)
        val = self.matcher.get_variable(var, set_if_none=0)
        self.value = val
        child = self.children[0]
        cval = child.to_value(skip=skip)
        if ExpressionUtility.is_none(cval):
            cval = 0
        else:
            cval = ExpressionUtility.to_float(cval)
        val += cval
        self.matcher.set_variable(var, value=val)
        self.value = val

    def _apply_default_value(self) -> None:
        var = self.first_non_term_qualifier(self.name)
        val = self.matcher.get_variable(var, set_if_none=0)
        self.value = val

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self._noop_match()
