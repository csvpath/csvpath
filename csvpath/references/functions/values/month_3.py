import calendar
from datetime import datetime

from ...reference_3 import Reference3
from ..function_3 import Function3
from .now_3 import Now3
from .time_window_function_3 import TimeWindowFunction3


class Month3(TimeWindowFunction3):
    # see year_3.py for the shared SOURCE == "clock" design this follows,
    # and TimeWindowFunction3 for the context-setter/anchor role added
    # 2026-10-17 (compendium 6.27). `calendar.monthrange()` gives the
    # current month's own last day (28-31, varies by month/leap year) --
    # stdlib, no new dependency.
    NAME = "month"
    SUMMARY = (
        "The current month as a 1-12 int -- computed from the clock. "
        "Also usable as a date-range context setter/anchor -- see "
        "TimeWindowFunction3."
        " Takes a time function to read the month of, or a month, e.g. :month(6)."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    # a time function to read the month of, or the month itself (6.27g),
    # as an int or a string of digits (an @variable from data)
    ARG_TYPES = (int, str, TimeWindowFunction3, Now3)
    COMPONENT = "month"
    ARG_REQUIRED = False
    SOURCE = "clock"
    # POSITIONS added 2026-10-17 -- see year_3.py's own comment for why.
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }

    def compute(self) -> int:
        return self.base_datetime().month

    def start_datetime(self) -> datetime:
        now = self.base_datetime()
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def end_datetime(self) -> datetime:
        now = self.base_datetime()
        last_day = calendar.monthrange(now.year, now.month)[1]
        return now.replace(
            day=last_day, hour=23, minute=59, second=59, microsecond=999999
        )
