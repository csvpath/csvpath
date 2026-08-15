from ...reference_3 import Reference3
from ..function_3 import Function3
from .date_3 import Date3
from .index_3 import Index3


class To3(Function3):
    #
    # the closing bound of :from()'s range -- see From3's own comment
    # for why the two are packaged together, the two independent index/
    # date modes, and why ARG_TYPES includes Index3/Date3. INCLUSIVE of
    # its own position/date (matches :index(n) pointing AT a position,
    # and SQL's BETWEEN, which David explicitly named as the model):
    # ":from(2):to(5)" is positions 2 through 5, both ends included,
    # five items total; ":to(:date('2025-01-31'))" includes runs that
    # arrived ON 2025-01-31 itself, not just before it.
    #
    NAME = "to"
    SUMMARY = (
        "The end of a range over the current scope's ordered items -- "
        "index-mode: up to and including this 0-based position "
        "(negative counts from the end), from the start or from "
        ":from()'s position if present. date-mode: up to and including "
        "this calendar date, compared against each run's own arrival "
        "date."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = (int, Index3, str, Date3)
    ARG_REQUIRED = True
    #
    # see From3's own POSITIONS comment -- always paired, same positions.
    #
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }
