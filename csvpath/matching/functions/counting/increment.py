# pylint: disable=C0114
from typing import Any
from csvpath.matching.util.exceptions import DataException
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Matchable
from ..function import Function
from ..args import Args


class Increment(ValueProducer):
    """increments a var every n-times each different value is seen"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
              increment() increases a variable tracking each match every N-matches.

              For example in a file with four lines of first names where there are
              two Johns, one Fred, and one Shen we would expect increment.john(#firstname=="John", 2)
              to create the variable john_increment with a value of 1.

              increment(), counter(), and every() are similar. counter() lets you add N each
              time a match component evaluates to True. increment() adds 1 each N times a
              match component evaluates to True. every() adds 1 every N-times a value is seen,
              matching or not.
            """
            ),
        ]
        self.name_qualifier = True
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(name="Match component", types=[Matchable], actuals=[Any])
        a.arg(name="Ratio", types=[Term], actuals=[int])
        self.args.validate(self.siblings())
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:  # pylint: disable=R0912
        # re: R0912: not pretty, but tested. whole needs to be reworked in
        # any case so we can get it into _produce_value() -- current
        # onmatch is too low.
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        tv = self.children[0].right.to_value()
        if not isinstance(tv, int):
            raise DataException(
                "increment value must be a positive int"
            )  # pragma: no cover
        tv = int(tv)
        if tv <= 0:
            raise DataException(
                "increment value must be a positive int"
            )  # pragma: no cover
        if not self.value:
            varname = self.first_non_term_qualifier(self.name)
            v = self.matcher.get_variable(varname)
            if v is None:
                v = 0
            v2 = v
            m = self.children[0].left.matches(skip=[self])
            om = self.onmatch
            lm = self.line_matches()
            if m:
                if om and lm:
                    v2 += 1
                elif not om:
                    v2 += 1
            r = 0
            incname = f"{varname}_increment"
            if v != v2:
                r = v2 % tv
                self.match = r == 0
                if self.match:
                    inc = v2 / tv
                    self.value = inc
                    self.matcher.set_variable(incname, value=inc)
                else:
                    inc = self.matcher.get_variable(incname)
                    if inc is None:
                        inc = 0
                    self.value = inc
                self.matcher.set_variable(varname, value=v2)
            else:
                self.match = False
                inc = self.matcher.get_variable(incname)
                if inc is None:
                    inc = 0
                self.value = inc
        return self.value

    def matches(self, *, skip=None) -> bool:
        self.to_value(skip=skip)
        return self.match
