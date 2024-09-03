# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import Term


class Stop(Function):
    def check_valid(self) -> None:
        self.validate_zero_or_more_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return False
        if self.match is None:
            self.match = True
            stopped = False
            if len(self.children) == 1:
                b = self.children[0].matches(skip=skip)
                if b is True:
                    self.matcher.csvpath.stop()
                    self.matcher.csvpath.logger.info(
                        f"stopping at {self.matcher.csvpath.line_monitor.physical_line_number}. contained child matches."
                    )
                    stopped = True
            else:
                self.matcher.csvpath.stop()
                self.matcher.csvpath.logger.info(
                    f"stopping at {self.matcher.csvpath.line_monitor.physical_line_number}"
                )
                stopped = True
            if stopped and self.name == "fail_and_stop":
                self.matcher.csvpath.logger.info("setting invalid")
                self.matcher.csvpath.is_valid = False
        return self.match


class Skip(Function):
    def check_valid(self) -> None:
        self.validate_zero_or_more_args()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return False
        if self.match is None:
            if not self.onmatch or self.line_matches():
                if not self.once or self.has_not_yet():
                    if len(self.children) == 1:
                        b = self.children[0].matches(skip=skip)
                        if b is True:
                            self.matcher.skip = True
                            if self.once:
                                self.set_has_happened()
                            self.matcher.csvpath.logger.info(
                                f"skipping physical line {self.matcher.csvpath.line_monitor.physical_line_number}. contained child matches."
                            )
                        else:
                            pass
                    else:
                        self.matcher.skip = True
                        if self.once:
                            self.set_has_happened()
                        self.matcher.csvpath.logger.info(
                            f"skipping line {self.matcher.csvpath.line_monitor.physical_line_number}"
                        )
                else:
                    pass
            else:
                pass
            self.match = True
        return self.match

        """
            #moved to matchable
            def has_not_yet(self):
                id = self.get_id()
                v = self.matcher.get_variable(id, set_if_none=True)
                return v

            def set_has_happened(self) -> None:
                id = self.get_id()
                self.matcher.set_variable(id, value=False)
        """
