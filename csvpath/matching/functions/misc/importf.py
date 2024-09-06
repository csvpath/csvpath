# pylint: disable=C0114
from typing import Any
from csvpath.matching.productions import Term
from csvpath.matching.util.exceptions import MatchComponentException
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import SideEffect


class Import(SideEffect):
    """imports one csvpath into another"""

    def check_valid(self) -> None:
        self.validate_one_arg(types=[Term])
        super().check_valid()
        self._inject()

    def _inject(self) -> None:
        #
        # we'll use self.value as our sentinel to make sure we
        # don't inject multiple times.
        #
        if self.value is None:
            #
            # the import goes here rather than in to_value so that it runs
            # before line 0
            #
            if self.matcher.csvpath.csvpaths is None:
                raise MatchComponentException("No CsvPaths instance available")

            name = self._value_one(skip=[self])
            if name is None:
                raise MatchComponentException("Name of import csvpath cannot be None")

            e = ExpressionUtility.get_my_expression(self)
            if e is None:
                raise MatchComponentException("Cannot find my expression: {self}")

            amatcher = self.matcher.csvpath.parse_named_path(name=name, disposably=True)
            if (
                amatcher is None
                or not amatcher.expressions
                or len(amatcher.expressions) == 0
            ):
                raise MatchComponentException("Parse named path failed: {name}")
            #
            # find where we do injection of the imported expressions
            #
            insert_at = -1
            pair = None
            for insert_at, pair in enumerate(self.matcher.expressions):
                if pair[0] == e:
                    break
            #
            # do the insert, swapping in our matcher for the original
            #
            for new_e in amatcher.expressions:
                self.matcher.expressions.insert(insert_at, new_e)
                new_e[0].matcher = self.matcher
            self.value = True

    def to_value(self, *, skip=None) -> Any:
        return self._noop_value()

    def matches(self, *, skip=None) -> bool:
        return self._noop_match()
