# pylint: disable=C0114
from typing import Any
from ..function_focus import SideEffect
from csvpath.matching.productions import Term, Header, Variable, Reference
from csvpath.matching.util.expression_utility import ExpressionUtility as exut
from csvpath.matching.util.exceptions import MatchException
from ..function import Function
from ..args import Args


class Rename(SideEffect):
    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                    Renames one or more headers for the duration of the run.

                    E.g. rename(#person, "fred") would make it possible to
                    use #fred as the header

                    This is most useful for files that have numeric values in the first line.
                    Setting header names is only syntactic sugar, but it can be helpful in adding
                    clarity, given that those files require the use of header indexes to access
                    values.

                    Rename() can also be a useful buffer if header order is likely to be correct but
                    header names may drift.

                    To reset three or more header names in order from left to right add more
                    names to the function args. However, if you only want to rename two headers
                    you must use two rename() calls.

                    Alternatively, you can use a stack variable. For example you could use a sequence
                    like this to update headers mid-run:
                        @headers = headers_stack()
                        line_number() == 3 -> reset_headers()
                        line_number() == 6 -> rename(@headers)

                    Note that renames do not affect other csvpaths, regardless of if they are run
                    in serial or breadth-first.
            """
            ),
        ]
        self.args = Args(matchable=self)
        #
        #
        #
        a = self.args.argset(1)
        a.arg(name="header", types=[Variable, Reference], actuals=[list, tuple])
        #
        #
        #
        a = self.args.argset(2)
        a.arg(name="header", types=[Header], actuals=[Any])
        a.arg(
            name="new name",
            types=[Term],
            actuals=[str],
        )
        #
        #
        #
        a = self.args.argset(2)
        a.arg(name="header name", types=[Term], actuals=[str])
        a.arg(
            name="new name",
            types=[Term],
            actuals=[str],
        )
        #
        #
        #
        a = self.args.argset(2)
        a.arg(name="header index", types=[Term], actuals=[int])
        a.arg(
            name="new name",
            types=[Term],
            actuals=[str],
        )
        #
        #
        #
        a = self.args.argset()
        a.arg(name="new header name", types=[Term], actuals=[str])
        #
        #
        #
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        sibs = self.siblings()
        if len(sibs) == 1:
            self._do_stack()
        elif len(sibs) > 2:
            self._do_all(skip=skip)
        else:
            self._do_one(skip=skip)
        self.match = self.default_match()

    def _do_stack(self, skip=None) -> None:
        s = self._value_one(skip=skip)
        if s is None:
            msg = "Cannot reset header names from a None stack var"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
            return
        self.matcher.csvpath.headers = s

    def _do_all(self, skip=None) -> None:
        sibs = self.siblings()
        for i, sib in enumerate(sibs):
            if i >= len(self.matcher.csvpath.headers):
                msg = f"Found rename() value at {i}, but that is greater than the number of headers"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
                break
            else:
                header = sib.to_value(skip=skip)
                self.matcher.csvpath.headers[i] = header

    def _do_one(self, skip=None) -> None:
        header = None
        c = self._child_one()
        if isinstance(c, Header):
            header = c.name
        else:
            header = self._value_one(skip=skip)
        i = exut.to_int(header)
        if not isinstance(header, int):
            i = self.matcher.header_index(header)

        val = self._value_two(skip=skip)

        self.matcher.csvpath.logger.debug(
            "Replacing %s idenified as %s with %s", self.matcher.line[i], header, val
        )
        if i >= len(self.matcher.csvpath.headers):
            msg = f"Found rename() value at {i}, but that is greater than the number of headers"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
        else:
            self.matcher.csvpath.headers[i] = val
