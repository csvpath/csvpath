from ...reference_3 import Reference3
from ..function_3 import Function3


class Date3(Function3):
    #
    # a literal calendar date, added 2026-08-13 as :from()/:to()'s
    # date-mode bound -- David: "arrival and run order is even more
    # important than indexing." DATE-only granularity for this pass
    # (a plain "YYYY-MM-DD" string, compared against a run's own
    # arrival date) -- hour/minute-level filtering (e.g. a future
    # ":yesterday(:hour(18))") is a separate, deferred extension of the
    # same comparison mechanism, not built here.
    #
    # ROLE is VALUE (it computes/holds a value, does not touch scope
    # itself) -- mirrors Index3's own role as an argument-only wrapper:
    # ":from(:date('2025-01-01'))" must give the same result as
    # ":from('2025-01-01')" (a bare date string, no wrapper), the same
    # "wrapper is optional but must be technically possible" pattern
    # already established for :from()/:index().
    #
    NAME = "date"
    SUMMARY = (
        "A literal calendar date (YYYY-MM-DD) -- used as :from()'s/"
        ":to()'s date-mode bound, e.g. ':from(:date(\"2025-01-01\"))' "
        "for 'runs from this date onward.'"
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = True
