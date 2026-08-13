from ...reference_3 import Reference3
from ..function_3 import Function3
from .index_3 import Index3


class To3(Function3):
    #
    # the closing bound of :from()'s range -- see From3's own comment
    # for why the two are packaged together and why ARG_TYPES includes
    # Index3. INCLUSIVE of its own position (matches :index(n) pointing
    # AT a position, and SQL's BETWEEN, which David explicitly named as
    # the model): ":from(2):to(5)" is positions 2 through 5, both ends
    # included, five items total.
    #
    NAME = "to"
    SUMMARY = (
        "The end of an index-based range over the current scope's "
        "ordered items -- up to and including this 0-based position "
        "(negative counts from the end), from the start or from "
        ":from()'s position if present."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (int, Index3)
    ARG_REQUIRED = True
