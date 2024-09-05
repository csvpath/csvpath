# pylint: disable=C0114
from csvpath.matching.util.exceptions import ChildrenException
from ..function import Function


class Failed(Function):
    """matches when the current file is in the failed/invalid state"""

    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        if self.name == "failed":
            self.value = not self.matcher.csvpath.is_valid
        elif self.name == "valid":
            self.value = self.matcher.csvpath.is_valid
        else:
            raise ChildrenException(f"Incorrect function name {self.name}")

    def matches(self, *, skip=None) -> bool:
        return self.to_value(skip=skip)
