from datetime import timedelta, datetime

from ...reference_3 import Reference3
from ..function_3 import Function3
from .time_window_function_3 import TimeWindowFunction3
from csvpath.util.date_util import DateUtility as daut


class Yesterday3(TimeWindowFunction3):
    # see today_3.py for the shared "YYYY-MM-DD" string format this
    # follows, and year_3.py for the shared SOURCE == "clock" design.
    # Extends TimeWindowFunction3 (added 2026-10-17, compendium 6.27/
    # 6.27f) -- the compendium's own flagship worked example for the
    # whole context-setter/anchor mechanism: bare
    # "$acme.files.:yesterday()" (a range, every file home with changes
    # within yesterday's window), ":yesterday():last()" (context for a
    # pointer), and "$acme.files.:from(:yesterday()):before(:today())"
    # (a directional anchor) are all settled, concrete acceptance
    # criteria -- see TimeWindowFunction3's own docstring for the
    # start()/end() rules confirmed against this exact example.
    NAME = "yesterday"
    SUMMARY = (
        "Yesterday's date as \"YYYY-MM-DD\" -- computed from the clock. "
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
        return (daut.now() - timedelta(days=1)).date().isoformat()

    def start_datetime(self) -> datetime:
        yesterday = (daut.now() - timedelta(days=1)).replace(tzinfo=None)
        return yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

    def end_datetime(self) -> datetime:
        yesterday = (daut.now() - timedelta(days=1)).replace(tzinfo=None)
        return yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
