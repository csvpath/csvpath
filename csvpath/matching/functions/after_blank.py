from typing import Any
from .function import Function


class AfterBlank(Function):
    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            if self.value is None:
                ll = self.matcher.csvpath.line_monitor.last_line
                if ll:
                    last_zero = ll.last_line_nonblank == 0
                    pline_no = self.matcher.csvpath.line_monitor.physical_line_number
                    lline_no = (
                        self.matcher.csvpath.line_monitor.last_line.last_data_line_number
                    )
                    if lline_no is None:
                        self.value = False
                    else:
                        cur_minus_last = pline_no - lline_no
                        ret = last_zero or cur_minus_last > 1
                        self.value = ret
                else:
                    #
                    # should be the first line.
                    #
                    self.value = False
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)