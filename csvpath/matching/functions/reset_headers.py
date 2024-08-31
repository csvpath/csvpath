from typing import Any
from .function import Function
from ..productions import ChildrenException


class ResetHeaders(Function):
    def check_valid(self) -> None:
        self.validate_zero_or_one_arg()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            self.matcher.csvpath.headers = self.matcher.line[:]
            self.matcher.header_dict = None
            for key in self.matcher.csvpath.variables.keys():
                #
                # if we checked for header name mismatches it happened just once
                # and is now invalid. we need to delete the vars and let it happen
                # again.
                #
                if (
                    key.endswith("_present")
                    or key.endswith("_unmatched")
                    or key.endswith("_duplicated")
                    or key.endswith("_misordered")
                ):
                    self.matcher.csvpath.logger.warning(
                        "Deleting variable {key} because it appears to be an out of date header name mismatch var."
                    )
                    del self.matcher.csvpath.variables[key]
            self.matcher.csvpath.logger.warning(
                f"Resetting headers mid run! Line number: {self.matcher.csvpath.line_monitor.physical_line_number}."
            )
            if len(self.children) == 1:
                self.children[0].matches(skip=skip)
            self.value = True
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)
