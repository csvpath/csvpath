# pylint: disable=C0114

from typing import Any
from csvpath.matching.productions import Equality
from csvpath.matching.util.exceptions import ChildrenException, MatchException
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import MatchDecider
from csvpath.matching.functions.function import Function
from csvpath.matching.productions.term import Term
from csvpath.matching.functions.types import (
    String,
    Nonef,
    Blank,
    Date,
    Decimal,
    Boolean,
    Wildcard,
)
from ..args import Args


class Line(MatchDecider):
    """checks that a line contains certain fields"""

    def check_valid(self) -> None:  # pragma: no cover
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(
            name="Header value types",
            types=[None, Wildcard, String, Boolean, Decimal, Date, Nonef, Blank],
            actuals=[None, Any],
        )
        sibs = self.siblings()
        self.args.validate(sibs)
        for i, s in enumerate(sibs):
            # check that no types are hiding non-headers
            if len(s.children) == 0:
                continue
            elif not isinstance(s.children[0], (Term, Equality)):
                # correct structure exception
                self.raiseChildrenException(
                    f"Unexpected {s}. line() expects only names of headers."
                )
            elif isinstance(s.children[0], Term):
                continue
            elif isinstance(s.children[0], Equality):
                ags = s.children[0].siblings()
                for a in ags:
                    if not isinstance(a, Term):
                        self.raiseChildrenException(
                            f"Unexpected {s}. line() expects only names of headers."
                        )
            else:
                self.raiseChildrenException(
                    f"Unexpected {s}. line() expects only names of headers."
                )
        super().check_valid()

    def _produce_value(self, skip=None) -> None:  # pragma: no cover
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        errors = []
        sibs = self.siblings()
        pln = self.matcher.csvpath.line_monitor.physical_line_number
        advance = 0
        advanced = 0
        for i, s in enumerate(sibs):
            pln = self.matcher.csvpath.line_monitor.physical_line_number
            if advance > 0:
                advance -= 1
                advanced += 1
                continue
            if isinstance(s, Equality):
                s = s._child_one()
            if self._handle_types_if(skip, i, s, errors):
                pass
            elif self._handle_blank_if(skip, i, s, errors):
                pass
            elif isinstance(s, Wildcard):
                advance = self._get_advance(skip, i, s, sibs)
            elif isinstance(s, Nonef):
                if not ExpressionUtility.is_none(self.matcher.line[i]):
                    errors.append(f"Line {pln}: position {i} is not empty")
            else:
                errors.append(
                    f"Line {pln}: unexpected type at position {ExpressionUtility._numeric_string(i)}: {s}"
                )

        found = len(sibs) + advanced + advance
        expected = len(self.matcher.csvpath.headers)
        if expected != found:
            self.raiseChildrenException(
                f"Line {pln}: Headers are wrong. Expected headers, including wildcards, is {expected}. Found {found}."
            )
        if len(errors) > 0:
            for e in errors:
                self.matcher.csvpath.print(e)
            me = MatchException(
                f"Line {pln}: structure of {self.my_chain} does not match"
            )
            # should we be hand delivering or raising? this way we don't get the full stack.
            self.my_expression.handle_error(me)
            self.match = False
        else:
            self.match = self.default_match()

    def _get_advance(self, skip, i, s, sibs) -> int:
        advance = 0
        v = s._value_one(skip=skip)
        if v is None or f"{v}".strip() == "*":
            advance = self._find_next_specified_header(skip, i, sibs)
            if advance == 0:
                advance = len(self.matcher.csvpath.headers) - i
            if advance is None:
                # pln = self.matcher.csvpath.line_monitor.physical_line_number
                self.raiseChildrenException(
                    "Line {pln}: Wildcard '{v}' at position {ExpressionUtility._numeric_string(i)} is not correct for line"
                )
        elif isinstance(v, int):
            advance = v
        else:
            v = ExpressionUtility.to_int(v, should_i_raise=False)
            if isinstance(v, int):
                advance = v
            else:
                # pln = self.matcher.csvpath.line_monitor.physical_line_number
                self.raiseChildrenException(
                    f"Wildcard '{v}' at position {ExpressionUtility._numeric_string(i)} has an unknown value"
                )
        # minus 1 for the wildcard itself
        advance -= 1
        return advance

    def _find_next_specified_header(self, skip, i, sibs):
        if i + 1 == len(sibs):
            return 0
        name = sibs[i + 1]._value_one(skip=skip)
        a = self.matcher.header_index(name)
        if a is None:
            return a
        return a - i

    def _handle_blank_if(self, skip, i, s, errors) -> bool:
        if not isinstance(s, (Blank)):
            return False
        pln = self.matcher.csvpath.line_monitor.physical_line_number
        t = s._value_one(skip=skip)
        if t is not None and t != self.matcher.csvpath.headers[i]:
            ii = i + 1
            errors.append(
                f"Line {pln}: the {ExpressionUtility._numeric_string(ii)} item, {t}, does not name a current header"
            )
        return True

    def _handle_types_if(self, skip, i, s, errors) -> bool:
        if not isinstance(s, (String, Decimal, Date, Boolean)):
            return False
        pln = self.matcher.csvpath.line_monitor.physical_line_number
        t = s._value_one(skip=skip)
        if t != self.matcher.csvpath.headers[i]:
            ii = i + 1
            errors.append(
                f"Line {pln}: the {ExpressionUtility._numeric_string(ii)} item, {t}, does not name a current header"
            )
        return True
