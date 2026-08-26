from ...reference_3 import Reference3
from ..function_3 import Function3
from csvpath.util.date_util import DateUtility as daut


class Hour3(Function3):
    # see year_3.py for the shared SOURCE == "clock" design this follows.
    # 12-hour clock, 1-12 -- see hour_24_3.py for the 24-hour sibling
    # (the compendium lists both as distinct functions).
    NAME = "hour"
    SUMMARY = "The current hour, 12-hour clock (1-12) -- computed from the clock."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "clock"

    def compute(self) -> int:
        return int(daut.now().strftime("%I"))
