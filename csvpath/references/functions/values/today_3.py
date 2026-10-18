from datetime import datetime

from ...reference_3 import Reference3
from ..function_3 import Function3
from .time_window_function_3 import TimeWindowFunction3
from csvpath.util.date_util import DateUtility as daut


class Today3(TimeWindowFunction3):
    # see year_3.py for the shared SOURCE == "clock" design this
    # follows. Returns a plain "YYYY-MM-DD" string, matching :date()'s
    # own established literal-date format (date_3.py) -- directly
    # usable as a path segment or interpolation value with no further
    # formatting decisions needed, rather than a raw Python datetime
    # (the compendium's own "datetime or str" for this function leaves
    # the choice open; str was chosen for consistency with :date()).
    # Extends TimeWindowFunction3 (added 2026-10-17, compendium 6.27/
    # 6.27f's own flagship example) -- the SAME window as Day3's own
    # (both mean "the current day"); see day_3.py for that extrapolation.
    NAME = "today"
    SUMMARY = (
        "Today's date as \"YYYY-MM-DD\" -- computed from the clock. "
        "Also usable as a date-range context setter/anchor -- see "
        "TimeWindowFunction3."
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

    def compute(self) -> str:
        return daut.now().date().isoformat()

    def start_datetime(self) -> datetime:
        now = daut.now().replace(tzinfo=None)
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    def end_datetime(self) -> datetime:
        now = daut.now().replace(tzinfo=None)
        return now.replace(hour=23, minute=59, second=59, microsecond=999999)
