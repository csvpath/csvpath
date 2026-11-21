from ...reference_3 import Reference3
from ..function_3 import Function3
from .clock_utility import ClockUtility as clut
from .now_3 import Now3
from .time_window_function_3 import TimeWindowFunction3


class MonthName3(Function3):
    # see year_3.py for the shared SOURCE == "clock" design this follows.
    NAME = "month_name"
    SUMMARY = (
        'The current month\'s full name, e.g. "August" -- computed from the clock.'
        " Takes a time function to read the month name of."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    # a time function to read the name of (6.27g; NRE ':day_name(:yesterday())')
    ARG_TYPES = (TimeWindowFunction3, Now3)
    ARG_REQUIRED = False
    SOURCE = "clock"

    def compute(self) -> str:
        return clut.base(function=self).strftime("%B")
