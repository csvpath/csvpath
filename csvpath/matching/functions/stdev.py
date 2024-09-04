# pylint: disable=C0114
from statistics import stdev, pstdev
from .function import Function
from ..productions import ChildrenException


class Stdev(Function):
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
        elif isinstance(v, str):
            stack = self.matcher.get_variable(v, set_if_none=[])
        else:
            raise ChildrenException(
                "Stdev must have 1 child naming a stack variable or returning a stack"
            )
        if stack is None or len(stack) == 0:
            pass
        else:
            if self.name == "pstdev":
                f = pstdev(self._to_floats(stack))
            else:
                f = stdev(self._to_floats(stack))
            f = float(f)
            f = round(f, 2)
        self.value = f

    def matches(self, *, skip=None) -> bool:
        self.to_value(skip=skip)
        return self._noop_match()  # pragma: no cover

    def _to_floats(self, stack):
        for i in range(0, len(stack)):  # pylint: disable=C0200
            # re: C0200 better to not mutate while iterating.
            # doesn't matter in this case, but still.
            try:
                stack[i] = float(stack[i])
            except (TypeError, ValueError):
                pass
        return stack
