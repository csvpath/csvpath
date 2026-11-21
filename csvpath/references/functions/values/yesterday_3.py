from ...reference_3 import Reference3
from ..function_3 import Function3
from .day_relative_function_3 import DayRelativeFunction3
from .now_3 import Now3
from .time_window_function_3 import TimeWindowFunction3


class Yesterday3(DayRelativeFunction3):
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

        " Takes a time function to count back from, e.g. :yesterday(:hour_24(18)), or a format string for the date, e.g. :yesterday(\"%A\")."    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    # a time function to start from, or a format string (6.27g); see
    # DayRelativeFunction3
    ARG_TYPES = (str, TimeWindowFunction3, Now3)
    DAYS_BACK = 1
    ARG_REQUIRED = False
    SOURCE = "clock"
    # POSITIONS added 2026-10-17 -- see year_3.py's own comment for why.
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }
