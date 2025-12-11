# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Header
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.functions.function import CheckedUnset
from ..args import Args


class LineBefore(ValueProducer):
    def check_valid(self) -> None:  # pylint: disable=W0246
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Tracks the most recent value of a header to enable comparison
                with the current value.
            """
            ),
        ]
        self.name_qualifier = True
        self.args = Args(matchable=self)
        self.args.argset(1).arg(name="header name", types=[Term], actuals=[str])
        self.args.argset(1).arg(name="header", types=[Header], actuals=[Any])
        self.args.validate(self.siblings())
        super().check_valid()  # pylint: disable=W0246

    def _produce_value(self, skip=None) -> None:
        var = self.first_non_term_qualifier(self.get_id())
        self.value = self.matcher.get_variable(var)
        if self.value is None:
            self.checked = CheckedUnset()
        c = self._child_one()
        header_name = c.name if isinstance(c, Header) else self._value_one(skip=skip)
        #
        # get and store the current value
        #
        v = self.matcher.get_header_value(header_name)
        self.matcher.set_variable(var, value=v)
        self.do_idem = False

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()  # pragma: no cover
