from ...reference_3 import Reference3
from ..function_3 import Function3
from csvpath.util.date_util import DateUtility as daut


class Today3(Function3):
    # see year_3.py for the shared SOURCE == "clock" design this
    # follows. Returns a plain "YYYY-MM-DD" string, matching :date()'s
    # own established literal-date format (date_3.py) -- directly
    # usable as a path segment or interpolation value with no further
    # formatting decisions needed, rather than a raw Python datetime
    # (the compendium's own "datetime or str" for this function leaves
    # the choice open; str was chosen for consistency with :date()).
    NAME = "today"
    SUMMARY = "Today's date as \"YYYY-MM-DD\" -- computed from the clock."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "clock"

    def compute(self) -> str:
        return daut.now().date().isoformat()
