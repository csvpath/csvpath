from datetime import timedelta

from ...reference_3 import Reference3
from ..function_3 import Function3
from csvpath.util.date_util import DateUtility as daut


class Yesterday3(Function3):
    # see today_3.py for the shared "YYYY-MM-DD" string format this
    # follows, and year_3.py for the shared SOURCE == "clock" design.
    NAME = "yesterday"
    SUMMARY = "Yesterday's date as \"YYYY-MM-DD\" -- computed from the clock."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "clock"

    def compute(self) -> str:
        return (daut.now() - timedelta(days=1)).date().isoformat()
