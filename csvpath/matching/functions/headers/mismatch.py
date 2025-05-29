# pylint: disable=C0114
from ..function_focus import ValueProducer
from csvpath.matching.productions.term import Term
from csvpath.matching.util.expression_utility import ExpressionUtility as exut
from ..args import Args


class Mismatch(ValueProducer):
    """tests the current headers against an expectation"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                mismatch() returns the number of headers in a row greater or less than the
                number expected. CsvPath uses the 0th row as headers; although, you can
                reset the headers at any point.

                Headers are like columns, except without any of the guarantees:

                - Expected headers may be missing from any given line

                - The number of headers per file is not fixed

                - There can be multiple header rows

                - The header line may not be the 0th line

                - Some lines can be blank and have no "cells" so no headers apply

                When the designated headers -- usually those set from the first non-blank line --
                do not match the number of values in a row there is a mismatch. The number of values
                means data values plus the empty string for those values that have a position in
                the line but no more substantial content.

                mismatch() counts the number of values, including blanks, compares that number to
                the number of headers, and returns the difference as a positive or signed integer.

                By default mismatch() returns the absolute value of the difference. If you pass
                a negative boolean (including "false", false(), and no()) or "signed" then mismatch()
                returns a negative number if the line has fewer delimited values than the current
                headers.

                If a line has no delimiters but does have whitespace characters it technically
                has one header. mismatch() doesn't give credit for the whitespace because in
                reality the line is blank and has zero headers.
            """
            ),
        ]

        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.argset(1).arg(name="a literal: signed", types=[Term], actuals=[str])
        self.args.argset(1).arg(name="signed", types=[Term], actuals=[bool])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        hs = len(self.matcher.csvpath.headers)
        ls = len(self.matcher.line)
        if ls == 1 and f"{self.matcher.line[0]}".strip() == "":
            # blank line with some whitespace chars. we don't take
            # credit for those characters.
            self.value = hs
        else:
            ab = True
            if len(self.children) == 1:
                v = self.children[0].to_value()
                if isinstance(v, str) and v.strip().lower() == "signed":
                    ab = False
                else:
                    ab = exut.to_bool(v)
            if ab:
                self.value = abs(hs - ls)
            else:
                signed = ls - hs
                self.value = signed

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip) != 0  # pragma: no cover
        #
        #
