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
            self.matcher.csvpath.advance_count = v
        except (TypeError, ValueError) as e:
            raise ChildrenException(
                f"Advance must contain an int, not {type(v)}"
            ) from e
        self.value = True

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip)


class AdvanceAll(Advance):
    """this class does an advance on this CsvPath and asks the CsvPaths
    instance, if any, to also advance all the following CsvPath
    instances
    """

    def _produce_value(self, skip=None) -> None:
        super()._produce_value(skip=skip)
        if self.matcher.csvpath.csvpaths:
            v = self._child_one().to_value(skip=skip)
            v = int(v)
            self.matcher.csvpath.csvpaths.advance_all(v)
