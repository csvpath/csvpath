# pylint: disable=C0114
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import SideEffect


class Advance(SideEffect):
    """this class lets a csvpath skip to a future line"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        v = child.to_value(skip=skip)
        try:
            v = int(v)
            self.matcher.csvpath.advance(v)
        except (TypeError, ValueError) as e:
            raise ChildrenException(
                f"Advance must contain an int, not {type(v)}"
            ) from e
        self.value = True

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip)
