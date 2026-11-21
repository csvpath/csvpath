from datetime import datetime

from ...reference_3 import Reference3
from ..function_3 import Function3
from .now_3 import Now3
from .time_window_function_3 import TimeWindowFunction3


class Minute3(TimeWindowFunction3):
    # see year_3.py for the shared SOURCE == "clock" design this
    # follows. Extends TimeWindowFunction3 (added 2026-10-17, compendium
    # 6.27).
    NAME = "minute"
    SUMMARY = (
        "The current minute (0-59) -- computed from the clock. Also "
        "usable as a date-range context setter/anchor -- see "
        "TimeWindowFunction3."
        " Takes a time function to read the minute of, or a minute, e.g. :minute(30)."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    # a time function to read the minute of, or the minute itself (6.27g),
    # as an int or a string of digits (an @variable from data)
    ARG_TYPES = (int, str, TimeWindowFunction3, Now3)
    COMPONENT = "minute"
    ARG_REQUIRED = False
    SOURCE = "clock"
    # POSITIONS added 2026-10-17 -- see year_3.py's own comment for why.
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }

    def compute(self) -> int:
        return self.base_datetime().minute

    def start_datetime(self) -> datetime:
        now = self.base_datetime()
        return now.replace(second=0, microsecond=0)

    def end_datetime(self) -> datetime:
        now = self.base_datetime()
        return now.replace(second=59, microsecond=999999)
