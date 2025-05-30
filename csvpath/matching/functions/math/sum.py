# pylint: disable=C0114
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.productions import Term, Variable, Header
from ..function_focus import ValueProducer
from ..function import Function
from ..args import Args


class Sum(ValueProducer):
    """returns the running sum of numbers"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Returns the running sum of a source.

                    sum() is similar to subtotal() but unlike subtotal
                    it does not use categorization to create multiple running totals.

                    Remember that CsvPath Language will convert None, bool, and the empty string
                    to int. This results in a predictable summation. If you are looking for a way
                    to make sure all lines have summable values try using integer() or another
                    approach.
                """
            ),
        ]
        self.name_qualifier = True
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="sum this",
            types=[Variable, Function, Term, Header],
            actuals=[int, float],
        )
        self.args.validate(self.siblings())
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
        self.match = self.default_match()
