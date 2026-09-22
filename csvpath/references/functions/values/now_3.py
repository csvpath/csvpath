from datetime import datetime

from ...reference_3 import Reference3
from ..function_3 import Function3
from csvpath.util.date_util import DateUtility as daut


class Now3(Function3):
    #
    # compendium 6.27/6.27g -- "the exact moment of interpretation to
    # the millisecond as a datetime object," used in string
    # interpolation to produce "a full datetime string." Unlike
    # Today3/Yesterday3 (deliberately coarse-grained "YYYY-MM-DD"
    # strings), :now() returns the real datetime object itself, per the
    # spec's own wording -- interpolation/path-building call sites
    # (reference_finder_3.py) already str() every compute() result
    # uniformly, so no separate stringification step is needed here.
    # See year_3.py for the shared SOURCE == "clock" design this
    # follows.
    #
    NAME = "now"
    SUMMARY = "The exact current moment, to the millisecond, as a datetime -- computed from the clock."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "clock"

    def compute(self) -> datetime:
        return daut.now()
