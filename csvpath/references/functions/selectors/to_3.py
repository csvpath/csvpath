from ...reference_3 import Reference3
from ..function_3 import Function3
from ..values.time_window_function_3 import TimeWindowFunction3
from .index_3 import Index3
from .name_3 import Name3


class To3(Function3):
    #
    # the closing bound of :from()'s range -- see From3's own comment
    # for why the two are packaged together, the two independent index/
    # date modes, and why ARG_TYPES includes Index3/TimeWindowFunction3.
    # INCLUSIVE of its own position/date (matches :index(n) pointing AT
    # a position, and SQL's BETWEEN, which David explicitly named as
    # the model): ":from(2):to(5)" is positions 2 through 5, both ends
    # included, five items total. A date bound is its first moment
    # (6.27b, 6.27g): ":to(:date('2025-01-31'))" includes runs up to
    # and at 2025-01-31 00:00:00, so it "effectively misses one day"
    # (normative examples; decision D8, 2026-11-12 -- it included the
    # whole 31st until then).
    #
    # ARG_TYPES widened 2026-10-17 from Date3 specifically to
    # TimeWindowFunction3 generically (compendium 6.27) -- ":to(:year())"/
    # ":to(:month())"/etc are now equally legal, using that function's
    # own start_datetime() as the inclusive upper cutoff (see
    # TimeWindowFunction3's own docstring for the rule; decision D8).
    # Date3 is itself a TimeWindowFunction3 now.
    #
    NAME = "to"
    SUMMARY = (
        "The end of a range over the current scope's ordered items -- "
        "index-mode: up to and including this 0-based position "
        "(negative counts from the end), from the start or from "
        ":from()'s position if present. date-mode: up to and including "
        "the first moment of this date or time-component function (e.g. "
        ":date('2026-01-31') is 2026-01-31 00:00:00, so the rest of that "
        "day is not included; :month() is the month's first moment), "
        "compared against each run's own arrival date."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    # Name3 added 2026-11-13: ':name("x")' is a statement identity in a
    # name_three range, the same as a bare string (NRE "Identities").
    # Only ReferenceFinder3._identity_bound() unwraps it; anywhere else a
    # ':name()' bound raises (see ReferenceFinder3._range_bound()).
    ARG_TYPES = (int, Index3, Name3, str, TimeWindowFunction3)
    ARG_REQUIRED = True
    #
    # see From3's own POSITIONS comment -- always paired, same positions.
    #
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }
