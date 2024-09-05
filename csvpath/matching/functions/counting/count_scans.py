# pylint: disable=C0114
from ..function import Function


class CountScans(Function):
    """the current number of lines scanned"""

    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matcher.csvpath.current_scan_count
