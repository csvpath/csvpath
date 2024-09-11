# pylint: disable=C0114
from statistics import stdev, pstdev
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import ValueProducer


class Stdev(ValueProducer):
    """takes the running sample or population standard deviation for a value"""

    def check_valid(self) -> None:
        self.validate_one_arg()
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
            raise ChildrenException(
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
        self.match = self._noop_match()  # pragma: no cover

    def _to_floats(self, stack):
        astack = []
        for i in range(0, len(stack)):  # pylint: disable=C0200
            astack.append(float(stack[i]))
        return astack
