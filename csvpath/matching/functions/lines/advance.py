# pylint: disable=C0114
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import SideEffect
from csvpath.matching.productions import Term, Variable
from csvpath.matching.functions.function import Function
from ..args import Args


class Advance(SideEffect):
    """this class lets a csvpath skip to a future line"""

    def check_valid(self) -> None:
        self.description = None
        if self.name == "advance":
            self.description = [
                self._cap_name(),
                self.wrap(
                    """\
                        Skips processing N-lines ahead. The lines skipped
                        will not be considered or collected as matched or unmatched.

                        advance() is similar to skip(). skip() cuts-short the processing of its line and
                        jumps to the next line. advance() skips N-number of whole lines after the line
                        where it is evaluated.
            """
                ),
            ]
        elif self.name == "advance_all":
            self.description = [
                self._cap_name(),
                self.wrap(
                    """\
                        Like advance(), advance_all() jumps processing N-lines forward. The lines
                        skipped will not be considered or collected as matched or unmatched.

                        advance_all() has the additional functionality of advancing all csvpaths
                        running breadth-first.

                        Csvpaths running breadth-first are in a named-paths group run
                        that was started using the collect_by_line(), fast_forward_by_line(), or
                        next_by_line() methods on the CsvPaths class.

                        advance_all() is similar to skip(). Acting in just one csvpath, skip()
                        cuts-short the processing of its line and jumps to the next line.
                        advance_all(), like advance(), finishes the line it is on within its
                        csvpath before jumping over the next N-lines.

                        However, similar to skip(), advance_all() stops the line it is evaluated
                        on from being fully considered because in a breadth-first run each csvpath
                        evaluates a line before the next line is started. advance_all() prevents
                        downstream csvpaths from seeing the line.

                        For example, take two csvpaths in a named-paths group that
                        was run using fast_forward_by_line(). If the first csvpath
                        uses a when/do operator to evaluate advance_all() on the odd lines, the
                        second csvpath will only see the even lines.
            """
                ),
            ]

        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(name="lines to advance", types=[Term, Variable, Function], actuals=[int])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        #
        # we want arg actual type checking so we have to call to_value
        # the action stays here, tho, because we are not providing value
        # to other match components, we're just a side-effect
        #
        self.to_value(skip=skip)
        child = self.children[0]
        v = child.to_value(skip=skip)
        v2 = ExpressionUtility.to_int(v)
        # would a non-int ever get past Args?
        """
        if not isinstance(v2, int):
            msg = f"Cannot convert {v} to an int"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
        """
        self.matcher.csvpath.advance_count = v2
        self.match = self.default_match()


class AdvanceAll(Advance):
    """this class does an advance on this CsvPath and asks the CsvPaths
    instance, if any, to also advance all the following CsvPath
    instances
    """

    def _decide_match(self, skip=None) -> None:
        super()._decide_match(skip=skip)
        if self.matcher.csvpath.csvpaths:
            v = self._child_one().to_value(skip=skip)
            v = int(v)
            self.matcher.csvpath.csvpaths.advance_all(v)
