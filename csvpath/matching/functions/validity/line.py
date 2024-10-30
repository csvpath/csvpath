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
)
from ..args import Args


class Line(MatchDecider):
    """checks that a line contains certain fields"""

    def check_valid(self) -> None:  # pragma: no cover
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(
            name="Header value types",
            types=[None, String, Boolean, Decimal, Date, Nonef, Blank],
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
                raise ChildrenException(
                    f"Unexpected {s}. line() expects only names of headers."
                )
            elif isinstance(s.children[0], Term):
                continue
            elif isinstance(s.children[0], Equality):
                ags = s.children[0].siblings()
                for a in ags:
                    if not isinstance(a, Term):
                        raise ChildrenException(
                            f"Unexpected {s}. line() expects only names of headers."
                        )
            else:
                raise ChildrenException(
                    f"Unexpected {s}. line() expects only names of headers."
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
            errors.append(
                f"Line {pln}: wrong number of headers. Expected {li}, not {hs}"
            )
        for i, s in enumerate(sibs):
            if isinstance(s, Equality):
                s = s._child_one()
            if isinstance(s, (String, Decimal, Date, Boolean)):
                t = s._value_one(skip=skip)
                if t != self.matcher.csvpath.headers[i]:
                    ii = i + 1
                    errors.append(
                        f"Line {pln}: the {ExpressionUtility._numeric_string(ii)} item, {t}, does not name a current header"
                    )
            else:
                if isinstance(s, (Blank)):
                    t = s._value_one(skip=skip)
                    if t is not None and t != self.matcher.csvpath.headers[i]:
                        ii = i + 1
                        errors.append(
                            f"Line {pln}: the {ExpressionUtility._numeric_string(ii)} item, {t}, does not name a current header"
                        )
                    else:
                        continue
                if isinstance(s, (Nonef)):
                    if ExpressionUtility.is_none(self.matcher.line[i]):
                        continue
                    errors.append(f"Line {pln}: position {i} is not empty")
                else:
                    errors.append(
                        f"Line {pln}: unexpected data type at position {i}: {s}"
                    )
        if len(errors) > 0:
            for e in errors:
                self.matcher.csvpath.print(e)
            me = MatchException(
                f"Line {pln}: structure of {self.my_chain} does not match"
            )
            # should we be hand delivering or raising. this way we don't get the full stack.
            self.my_expression.handle_error(me)
            self.match = False
        else:
            self.match = self.default_match()
