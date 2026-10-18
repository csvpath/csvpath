from datetime import datetime

from ...reference_3 import Reference3
from ..function_3 import Function3
from .time_window_function_3 import TimeWindowFunction3
from csvpath.util.date_util import DateUtility as daut


class Hour243(TimeWindowFunction3):
    # see year_3.py for the shared SOURCE == "clock" design this
    # follows, and hour_3.py for the 12-hour sibling. Extends
    # TimeWindowFunction3 (added 2026-10-17, compendium 6.27) -- same
    # window as Hour3's own (there is only one "current hour"), just
    # the 24-hour sibling's own compute() value differs.
    NAME = "hour_24"
    SUMMARY = (
        "The current hour, 24-hour clock (0-23) -- computed from the "
        "clock. Also usable as a date-range context setter/anchor -- "
        "see TimeWindowFunction3."
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
        return daut.now().hour

    def start_datetime(self) -> datetime:
        now = daut.now().replace(tzinfo=None)
        return now.replace(minute=0, second=0, microsecond=0)

    def end_datetime(self) -> datetime:
        now = daut.now().replace(tzinfo=None)
        return now.replace(minute=59, second=59, microsecond=999999)
