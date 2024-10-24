# pylint: disable=C0114
from statistics import stdev, pstdev
from csvpath.matching.util.exceptions import DataException
from csvpath.matching.productions import Variable, Term
from ..function import Function
from ..function_focus import ValueProducer
from ..args import Args


class Stdev(ValueProducer):
    """takes the running sample or population standard deviation for a value"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(types=[Variable, Function, Term], actuals=[str, tuple, list])
        self.args.validate(self.siblings_or_equality())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        v = self.children[0].to_value(skip=skip)
        stack = None
        f = None
        if isinstance(v, list):
            stack = v
        #
        # frozen vars at end of run may be tupleized due to a blank end line
        #
        elif isinstance(v, (str, tuple)):
            stack = self.matcher.get_variable(v, set_if_none=[])
        else:
            # this could be a data or structure / children exception. since
            # we except non-Terms that produce the name it is better as a
            # Args-type / data exception.
            raise DataException(
                "Stdev must have 1 child naming a stack variable or returning a stack"
            )
        if len(stack) == 0:
            pass
        else:
            if self.name == "pstdev":
                f = pstdev(self._to_floats(stack))
            else:
                f = stdev(self._to_floats(stack))
            f = float(f)
            f = round(f, 2)
        self.value = f

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)  # pragma: no cover
        self.match = self.default_match()  # pragma: no cover

    def _to_floats(self, stack):
        astack = []
        for i in range(0, len(stack)):  # pylint: disable=C0200
            astack.append(float(stack[i]))
        return astack
