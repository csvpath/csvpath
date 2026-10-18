from datetime import datetime

from ...reference_3 import Reference3
from ..function_3 import Function3
from .time_window_function_3 import TimeWindowFunction3
from csvpath.util.date_util import DateUtility as daut


class Day3(TimeWindowFunction3):
    # see year_3.py for the shared SOURCE == "clock" design this follows,
    # and TimeWindowFunction3 for the context-setter/anchor role added
    # 2026-10-17 (compendium 6.27). As a date range this is "today" --
    # extrapolated from :year()/:month() each meaning "the current
    # period at that granularity" (no worked example pins this down
    # explicitly, unlike :yesterday()'s own compendium 6.27f).
    NAME = "day"
    SUMMARY = (
        "The current day of the month as a 1-31 int -- computed from "
        "the clock. Also usable as a date-range context setter/anchor, "
        "same window as :today() -- see TimeWindowFunction3."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "clock"
    # POSITIONS added 2026-10-17 -- see year_3.py's own comment for why.
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }

    def compute(self) -> int:
        return daut.now().day

    def start_datetime(self) -> datetime:
        now = daut.now().replace(tzinfo=None)
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    def end_datetime(self) -> datetime:
        now = daut.now().replace(tzinfo=None)
        return now.replace(hour=23, minute=59, second=59, microsecond=999999)
