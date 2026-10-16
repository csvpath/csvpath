from ...reference_3 import Reference3
from ..function_3 import Function3
from .date_3 import Date3
from .index_3 import Index3


class After3(Function3):
    #
    # the EXCLUSIVE sibling of :from() -- compendium 6.28/6.28b/6.28c,
    # built 2026-10-16. See Before3's own comment for the shared
    # mechanism/alias-registration reasoning; this is the LOWER-bound
    # mirror of it. ":after(5)" starts at position 6, not 5;
    # ":after(:date('2025-01-31'))" excludes runs that arrived ON
    # 2025-01-31 itself, only strictly later ones. Aliased "above"/"gt"
    # (6.28b).
    #
    # 6.28c: combining with :from() (another LOWER bound) is illegal.
    # May pair with :before()/:to() (an UPPER bound) to form a range.
    #
    NAME = "after"
    SUMMARY = (
        "The exclusive start of a range over the current scope's "
        "ordered items -- index-mode: from, but NOT including, this "
        "0-based position (negative counts from the end) to the end, "
        "or to :before()'s/:to()'s position if present. date-mode: "
        "from, but not including, this calendar date onward, compared "
        "against each run's own arrival date. Aliases: ':above()'/"
        "':gt()'."
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
