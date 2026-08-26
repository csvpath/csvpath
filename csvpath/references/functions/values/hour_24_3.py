from ...reference_3 import Reference3
from ..function_3 import Function3
from csvpath.util.date_util import DateUtility as daut


class Hour243(Function3):
    # see year_3.py for the shared SOURCE == "clock" design this
    # follows, and hour_3.py for the 12-hour sibling.
    NAME = "hour_24"
    SUMMARY = "The current hour, 24-hour clock (0-23) -- computed from the clock."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "clock"

    def compute(self) -> int:
        return daut.now().hour
