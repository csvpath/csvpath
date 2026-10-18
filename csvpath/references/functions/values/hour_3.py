from datetime import datetime

from ...reference_3 import Reference3
from ..function_3 import Function3
from .time_window_function_3 import TimeWindowFunction3
from csvpath.util.date_util import DateUtility as daut


class Hour3(TimeWindowFunction3):
    # see year_3.py for the shared SOURCE == "clock" design this
    # follows, and hour_24_3.py for the 24-hour sibling. 12-hour clock,
    # 1-12 -- the compendium lists both as distinct functions. Extends
    # TimeWindowFunction3 (added 2026-10-17, compendium 6.27) -- the
    # start/end window is always computed from the real 24-hour value
    # (daut.now().hour), not the 12-hour display value compute()
    # returns -- there is only one "current hour" to window, regardless
    # of which of the two clock conventions names it.
    NAME = "hour"
    SUMMARY = (
        "The current hour, 12-hour clock (1-12) -- computed from the "
        "clock. Also usable as a date-range context setter/anchor "
        "(the real current hour, not a display convention) -- see "
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

    def compute(self) -> int:
        return int(daut.now().strftime("%I"))

    def start_datetime(self) -> datetime:
        now = daut.now().replace(tzinfo=None)
        return now.replace(minute=0, second=0, microsecond=0)

    def end_datetime(self) -> datetime:
        now = daut.now().replace(tzinfo=None)
        return now.replace(minute=59, second=59, microsecond=999999)
