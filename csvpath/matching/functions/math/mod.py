# pylint: disable=C0114
import math
from decimal import Decimal, InvalidOperation
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Header, Variable, Reference
from ..function import Function
from ..args import Args


class Mod(ValueProducer):
    """takes the modulo of numbers"""

    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                    Calculates the modulo of two numbers.
            """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="dividend",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[int, float],
        )
        a.arg(
            name="divisor",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[int, float],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        ret = 0
        v = siblings[0].to_value(skip=skip)
        m = siblings[1].to_value(skip=skip)
        #
        # the float modulo comes first so that bad input, zero divisors, and
        # infinities behave and raise exactly as they always have
        #
        fv = float(v)
        fm = float(m)
        ret = fv % fm
        #
        # float noise makes e.g. 0.3 % 0.1 come out as 0.0999..., so for
        # finite operands the remainder is recomputed exactly from each
        # float's shortest decimal form (issue #305)
        #
        if math.isfinite(fv) and math.isfinite(fm):
            try:
                d = Decimal(repr(fv)) % Decimal(repr(fm))
                #
                # Decimal's remainder takes the dividend's sign; Python's float
                # modulo takes the divisor's. keep Python's.
                #
                if d != 0 and (d < 0) != (fm < 0):
                    d += Decimal(repr(fm))
                ret = float(d)
            except InvalidOperation:
                #
                # the quotient is too large for an exact Decimal remainder;
                # keep the float result
                #
                pass
        self.value = ret

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()
