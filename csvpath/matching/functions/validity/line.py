# pylint: disable=C0114

from typing import Any
from csvpath.matching.productions import Equality
from csvpath.matching.util.exceptions import ChildrenException, MatchException
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.functions.function import Function
from csvpath.matching.productions.term import Term
from csvpath.matching.functions.types import (
    String,
    Nonef,
    Blank,
    Date,
    Decimal,
    Boolean,
    Email,
    Url,
    Wildcard,
)
from ..args import Args
from ..function_focus import MatchDecider
from ..lines.dups import FingerPrinter


class Line(MatchDecider):
    """checks that a line contains certain fields"""

    def check_valid(self) -> None:  # pragma: no cover
        self.name_qualifier = True
        self.match_qualifiers.append("distinct")
        # removes onmatch from list. having not looked at this for a while, why?
        self.value_qualifiers = []
        self.description = [
            self._cap_name(),
            "line() creates structural schema definitions.",
            self.wrap(
                """\
                Each line() function represents an entire line of the data
                file.

                Using wildcards and blanks allows a line() to specify
                just certain headers, rather than explicitly defining
                header-by-header. This also allows for more line() functions
                to specify other structures within the same data. You could,
                for e.g., define a person line() and an address line() that
                lives side by side in the same rows."""
            ),
        ]

        self.args = Args(matchable=self)
        a = self.args.argset()
        types = [
            None,
            Wildcard,
            String,
            Boolean,
            Decimal,
            Date,
            Nonef,
            Blank,
            Email,
            Url,
        ]
        a.arg(
            name="function representing a data type",
            types=types,
            actuals=[None, Any],
        )
        sibs = self.siblings()

        error_types = []
        for s in sibs:
            isin = isinstance(s, tuple(types))
            if not isin:
                error_types.append(s.name)

        if len(error_types) > 0:
            et = f"{error_types}"
            et = et.replace("[", "")
            et = et.replace("]", "")
            et = et.replace("'", "")
            msg = f"Incorrect types in line definition: {et}"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise:
                raise ChildrenException(msg)
        self.args.validate(sibs)
        super().check_valid()

    def _produce_value(self, skip=None) -> None:  # pragma: no cover
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        errors = []
        #
        # validation work happens here
        #
        found = self._count_headers(errors=errors)
        expected = len(self.matcher.csvpath.headers)
        #
        # here down is error handling and signaling results
        #
        if expected != found:
            msg = f"Headers are wrong. Expected headers, including wildcards: {expected}. Found {found}."
            errors.append(msg)
        for e in errors:
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=e)
        if len(errors) > 0:
            msg = f"{len(errors)} errors in line()"
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
            self.match = False
        elif self._distinct_if(skip=skip):
            pass
        else:
            self.match = self.default_match()

    # =======================================
    #
    #

    def _count_headers(self, *, errors, skip=None) -> None:
        sibs = self.siblings()
        #
        # advance is set by wildcard and we skip headers that are advanced over
        #
        advance = 0
        advanced = 0
        advance_max = 0
        for i, s in enumerate(sibs):
            if advance > 0:
                advance -= 1
                advanced += 1
            if isinstance(s, Equality):
                s = s._child_one()
            #
            # from here down we are checking
            #   header:             i+advanced
            #   vs match component: i
            #
            if self._handle_types_if(
                skip, i, s, errors, advanced=advanced, advance_max=advance_max
            ):
                pass
            elif self._handle_blank_if(skip, i, s, errors):
                pass
            elif isinstance(s, Wildcard):
                advance = self._get_advance(
                    skip,
                    i,
                    s,
                    sibs,
                    advanced=advanced,
                    advance=advance,
                    advance_max=advance_max,
                )
                if advance > advance_max:
                    advance_max = advance
            elif isinstance(s, Nonef):
                if not ExpressionUtility.is_none(self.matcher.line[i]):
                    msg = f"Position {i} is not empty"
                    errors.append(msg)
            else:
                msg = f"Unexpected type at position {i}: {s}"
                errors.append(msg)
            b = s.matches(skip=skip)
            if b is not True:
                msg = f"Invalid value at {s.my_chain}"
                errors.append(msg)
        found = len(sibs) + advanced + advance
        return found

    def _distinct_if(self, skip) -> None:
        if self.distinct:
            name = self.first_non_term_qualifier(self.name)
            sibs = self.sibling_values()
            fingerprint, lines = FingerPrinter._capture_line(
                self, name, skip=skip, sibs=sibs
            )
            if len(lines) > 1:
                msg = "Duplicate line found where a distict set of values is expected"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)

    def _get_advance(
        self,
        skip,
        i,
        s,
        sibs,
        *,
        advanced: int = 0,
        advance: int = 0,
        advance_max: int = 0,
    ) -> int:
        advance = 0
        if i == len(sibs) - 1:
            hs = len(self.matcher.csvpath.headers)
            a = i + advanced + advance
            f = hs - a
            # minus 1 for the wildcard itself
            ret = f - 1
            # wildcard is last. we don't care if there is more stuff, we're done w/line().
            return ret
        v = s._value_one(skip=skip)
        if v is None or f"{v}".strip() == "*":
            advance = self._find_next_specified_header(skip, i, sibs)
            if advance == 0:
                advance = len(self.matcher.csvpath.headers) - i
            if advance is None:
                msg = f"Wildcard '{v}' at position {ExpressionUtility._numeric_string(i)} "
                msg = f"{msg}is not correct for line"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
        elif isinstance(v, int):
            advance = v
        else:
            v2 = ExpressionUtility.to_int(v)  # , should_i_raise=False
            if not isinstance(v2, int):
                msg = f"Wildcard cannot convert {v} to an int"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
            advance = v2
        if not isinstance(advance, int):
            # just returning 0 because we should have already reported this problem.
            return 0
        # minus 1 for the wildcard itself
        advance -= 1
        return advance

    def _find_next_specified_header(self, skip, i, sibs):
        if i + 1 == len(sibs):
            return 0
        name = sibs[i + 1]._child_one().name
        a = self.matcher.header_index(name)
        if a is None:
            return a
        return a - i

    def _handle_blank_if(self, skip, i, s, errors) -> bool:
        if not isinstance(s, (Blank)):
            return False
        t = s._child_one()
        #
        # if t is a named header check that. if it is a numbered header
        #
        if t and t.name != self.matcher.csvpath.headers[i] and t.name != f"{i}":
            ii = i + 1
            msg = f"The {ExpressionUtility._numeric_string(ii)} item, {t}, does not match the current header"
            errors.append(msg)
        return True

    def _handle_types_if(
        self, skip, i, s, errors, *, advanced=-1, advance_max=-1
    ) -> bool:
        if not isinstance(s, (String, Decimal, Date, Boolean, Email, Url)):
            return False
        t = s._child_one()
        i = advance_max + i
        #
        # we need i+advanced in order to pick the right header
        #
        if t and t.name != self.matcher.csvpath.headers[i] and t.name != f"{i}":
            ii = i + 1
            msg = f"The {ExpressionUtility._numeric_string(ii)} item, {t}, does not match the current header"
            errors.append(msg)
        return True
