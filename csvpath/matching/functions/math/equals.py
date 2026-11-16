# pylint: disable=C0114
from typing import Any
from ..function_focus import MatchDecider
from ..args import Args
from ..function import Function
from csvpath.matching.productions import Header, Variable, Reference, Term


class Equals(MatchDecider):
    """tests the equality of two values. in most cases you don't
    need a function to test equality but in some cases it may
    help with clarity or a corner case that can't be handled
    better another way."""

    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                f"""\
                    Tests the equality of two values.

                    In most cases you will use == to test equality. However, in some cases
                    {self.name}() gives more flexibility.

                    Moreover, in one case, you must use the function, not ==. Using {self.name}()
                    is required in order to set a variable to the value of an equality test.

                    In other words, to set @a equal to the equality test of @b to the string "c", you must do:
                    @a = {self.name}(@b, "c"). @a = @b == "c" is not allowed.
            """
            ),
        ]
        if self.name in ["equal", "equals", "eq"]:
            self.aliases = ["equal", "equals", "eq"]
        elif self.name in ["neq", "not_equal_to"]:
            self.aliases = ["neq", "not_equal_to"]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="is this",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[Any],
        )
        a.arg(
            name="equal to that",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[Any],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        child = self.children[0]
        ret = False
        left = child.left.to_value(skip=skip)
        right = child.right.to_value(skip=skip)
        #
        # a missing value (None or "") never equals a present value. two
        # missing values are compared below as before: None == None and
        # "" == "", but "" != None. this used to be a truthiness test, so a
        # falsy but real value like 0 was treated as missing: eq("0", 0) was
        # False while eq(1, "1.0") was True.
        #
        if self._missing(left) != self._missing(right):
            ret = False
        elif left is None and right is None:
            ret = True
        elif self._is_float(left) and self._is_float(right):
            ret = float(left) == float(right)
        elif f"{left}" == f"{right}":
            ret = True
        else:
            ret = False
        if self.name in ["neq", "not_equal_to"]:
            ret = not ret
        self.match = ret

    def _missing(self, v) -> bool:
        return v is None or (isinstance(v, str) and v == "")

    def _is_float(self, fs) -> bool:
        try:
            float(fs)
        except (OverflowError, ValueError, TypeError):
            #
            # TypeError: float(None) or float([]). eq(0, none()) raised it.
            #
            return False
        return True
