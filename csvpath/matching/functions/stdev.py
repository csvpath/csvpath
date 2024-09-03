# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import ChildrenException
from statistics import stdev, pstdev


class Stdev(Function):
    """takes the running sample or population standard deviation for a value"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if len(self.children) != 1:
            raise ChildrenException(
                "Stdev must have 1 child naming a stack variable or returning a stack"
            )

        if self.value is None:
            om = self.has_onmatch()
            if not om or self.line_matches():
                child = self.children[0]
                v = child.to_value()
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
        return self.value

    def matches(self, *, skip=None) -> bool:
        self.to_value(skip=skip)
        return self._noop_match()  # pragma: no cover

    def _to_floats(self, stack):
        for i in range(0, len(stack)):
            try:
                stack[i] = float(stack[i])
            except Exception:
                pass
        return stack
