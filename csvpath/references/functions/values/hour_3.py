from datetime import datetime

from ...reference_3 import Reference3
from ..function_3 import Function3
from ...reference_exceptions_3 import ReferenceException3
from .now_3 import Now3
from .time_window_function_3 import TimeWindowFunction3


class Hour3(TimeWindowFunction3):
    # see year_3.py for the shared SOURCE == "clock" design this
    # follows, and hour_24_3.py for the 24-hour sibling. 12-hour clock,
    # 1-12 -- the compendium lists both as distinct functions. Extends
    # TimeWindowFunction3 (added 2026-10-17, compendium 6.27) -- the
    # start/end window is always computed from the real 24-hour value
    # (self.base_datetime().hour), not the 12-hour display value compute()
    # returns -- there is only one "current hour" to window, regardless
    # of which of the two clock conventions names it.
    NAME = "hour"
    SUMMARY = (
        "The current hour, 12-hour clock (1-12) -- computed from the "
        "clock. Also usable as a date-range context setter/anchor "
        "(the real current hour, not a display convention) -- see "
        "TimeWindowFunction3."
        " Takes a time function to read the hour of; for a given hour use :hour_24()."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    # a time function to read the hour of (6.27g). ':hour()' is the
    # 12-hour clock; an hour is set with ':hour_24(n)' (David, 2026-11-22,
    # D40 h). So a number never sets an hour here: 1-12 cannot say am or
    # pm, and 0 and 13-23 are not 12-hour values. int stays in ARG_TYPES so
    # a number gets the message that points to ':hour_24()', not a type
    # error. (Until 2026-11-22, 0 and 13-23 were taken as 24-hour values.)
    ARG_TYPES = (int, str, TimeWindowFunction3, Now3)
    COMPONENT = "hour"
    ARG_REQUIRED = False
    SOURCE = "clock"
    # POSITIONS added 2026-10-17 -- see year_3.py's own comment for why.
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }

    def check_valid(self) -> None:
        self._check_not_ambiguous(self._arg)
        super().check_valid()

    def base_datetime(self) -> datetime:
        # again for an @variable's value, only known once resolved
        self._check_not_ambiguous(self.arg)
        return super().base_datetime()

    @staticmethod
    def _check_not_ambiguous(arg) -> None:
        if isinstance(arg, bool):
            return
        if isinstance(arg, str) and arg.strip().isdigit():
            arg = int(arg.strip())
        if not isinstance(arg, int):
            return
        if 1 <= arg <= 12:
            raise ReferenceException3(
                f":hour({arg}) is ambiguous: :hour() is the 12-hour clock, so "
                f"{arg} could be am or pm. Use :hour_24({arg % 12}) or "
                f":hour_24({arg % 12 + 12})."
            )
        if arg == 0 or 13 <= arg <= 23:
            raise ReferenceException3(
                f":hour({arg}) does not set an hour: :hour() is the 12-hour "
                f"clock. Use :hour_24({arg}) for a 24-hour hour."
            )
        raise ReferenceException3(
            f":hour({arg}) does not set an hour, and {arg} is not an hour: "
            ":hour() is the 12-hour clock; :hour_24() takes 0-23."
        )

    def compute(self) -> int:
        return int(self.base_datetime().strftime("%I"))

    def start_datetime(self) -> datetime:
        now = self.base_datetime()
        return now.replace(minute=0, second=0, microsecond=0)

    def end_datetime(self) -> datetime:
        now = self.base_datetime()
        return now.replace(minute=59, second=59, microsecond=999999)
