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

        " Takes a time function to read the hour of; for a given hour use :hour_24()."    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    # a time function to read the hour of (6.27g). An int is refused in
    # check_valid(): a 12-hour value cannot say am or pm, so ':hour(6)'
    # would be a guess; the hour itself is ':hour_24(18)'
    ARG_TYPES = (int, TimeWindowFunction3, Now3)
    ARG_REQUIRED = False
    SOURCE = "clock"
    # POSITIONS added 2026-10-17 -- see year_3.py's own comment for why.
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }

    def check_valid(self) -> None:
        if isinstance(self._arg, int) and not isinstance(self._arg, bool):
            raise ReferenceException3(
                f":hour({self._arg}) is ambiguous: :hour() is the 12-hour clock, "
                "so a number cannot say am or pm. Use :hour_24(), e.g. "
                ":hour_24(18) for 6pm."
            )
        super().check_valid()

    def compute(self) -> int:
        return int(self.base_datetime().strftime("%I"))

    def start_datetime(self) -> datetime:
        now = self.base_datetime()
        return now.replace(minute=0, second=0, microsecond=0)

    def end_datetime(self) -> datetime:
        now = self.base_datetime()
        return now.replace(minute=59, second=59, microsecond=999999)
