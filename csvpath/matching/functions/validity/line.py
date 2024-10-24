# pylint: disable=C0114

from typing import Any
from csvpath.matching.productions import Equality
from csvpath.matching.util.exceptions import ChildrenException, MatchException
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import MatchDecider
from csvpath.matching.functions.function import Function
from csvpath.matching.productions.header import Header
from csvpath.matching.functions.strings.string import String
from csvpath.matching.functions.misc.nonef import Nonef, Blank
from csvpath.matching.functions.dates.datef import Date
from csvpath.matching.functions.math.intf import Num, Float, Int
from csvpath.matching.functions.boolean.boolean import Boolean
from ..args import Args


class Line(MatchDecider):
    """checks that a line contains certain fields"""

    def check_valid(self) -> None:  # pragma: no cover
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(types=[None, Function, Header], actuals=[Any])
        sibs = self.siblings()
        self.args.validate(sibs)
        for s in sibs:
            if isinstance(s, Header):
                continue
            elif not isinstance(
                s, (String, Boolean, Int, Float, Num, Date, Nonef, Blank)
            ):
                # correct structure exception
                raise ChildrenException(f"Unexpected {s}")
            else:
                # check that no types are hiding non-headers
                if len(s.children) == 0:
                    continue
                elif not isinstance(s.children[0], Header):
                    # correct structure exception
                    raise ChildrenException(
                        f"Unexpected {s}. line() expects only header definitions."
                    )

        super().check_valid()

    def _produce_value(self, skip=None) -> None:  # pragma: no cover
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        errors = []
        sibs = self.siblings()
        li = len(sibs)
        hs = len(self.matcher.csvpath.headers)
        pln = self.matcher.csvpath.line_monitor.physical_line_number
        if not li == hs:
            me = MatchException(
                f"Line {pln}: wrong number of headers. Expected {li} but found {hs}"
            )
            self.my_expression.handle_error(me)
        for i, s in enumerate(sibs):
            if isinstance(s, Header):
                if s.name != self.matcher.csvpath.headers[i]:
                    errors.append(
                        f"Line {pln}: the {ExpressionUtility._numeric_string(i)} item, {s.name}, does not name a current header"
                    )
                elif not s.matches(skip=skip):
                    errors.append(
                        f"Line {pln}: the {ExpressionUtility._numeric_string(i)} item, {s.name}, does not match"
                    )
            else:
                if isinstance(s, (Blank, Nonef)):
                    continue
                if s.children[0].name != self.matcher.csvpath.headers[i]:
                    errors.append(
                        f"Line {pln}: the {ExpressionUtility._numeric_string(i)} item, {s.children[0].name}, does not name a current header"
                    )
                elif not s.matches(skip=skip):
                    # we shouldn't need this because we're restricting the functs and their
                    # children to things that will trigger arg validation
                    # errors.append(f"Line {pln}: the {self._numeric_string(i)} item, {s.children[0].name}, does not match")
                    pass
        if len(errors) > 0:
            for e in errors:
                self.matcher.csvpath.print(e)
            me = MatchException(f"Line {pln} does not match")
            self.my_expression.handle_error(me)
        self.match = self.default_match()
