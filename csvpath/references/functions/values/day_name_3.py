from ...reference_3 import Reference3
from ..function_3 import Function3
from csvpath.util.date_util import DateUtility as daut


class DayName3(Function3):
    # see year_3.py for the shared SOURCE == "clock" design this follows.
    NAME = "day_name"
    SUMMARY = "The current day of the week's full name, e.g. \"Wednesday\" -- computed from the clock."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "clock"

    def compute(self) -> str:
        return daut.now().strftime("%A")
