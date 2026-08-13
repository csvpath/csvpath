from ...reference_3 import Reference3
from ..function_3 import Function3
from .date_3 import Date3
from .index_3 import Index3


class From3(Function3):
    #
    # a range selector -- added 2026-08-13, RESULTS only for now (the
    # doc's own confirmed examples are all RESULTS; FILES/CSVPATHS get
    # this later if a concrete need shows up, per this session's own
    # "build only what's confirmed" discipline). Packaged together with
    # :to() on purpose (David: "our version of BETWEEN in SQL or
    # range() in Python... I'd only separate them if there is some
    # underlying implementation detail that makes them better tackled
    # as two things" -- there isn't; both narrow an already-ordered
    # candidate list, :from() sets the start bound, :to() the end
    # bound). Two independent MODES, picked by which arg type is given
    # -- index-mode (int/Index3, see ReferenceFinder3._range_bound()):
    # positional, "from this 0-based position to the end." date-mode
    # (str/Date3, added the same day David asked for it specifically --
    # "arrival and run order is even more important than indexing"):
    # "from this calendar date onward," compared against each run's own
    # arrival date (see ResultsReferenceFinder3._apply_date_range()).
    # The two modes are never mixed within one :from()/:to() pair --
    # query() rejects that combination explicitly.
    #
    # ARG_TYPES includes Index3/Date3, not just int/str, because the
    # doc's own NOTES block explicitly requires ":from(:index(-3))" to
    # be legal and identical to ":from(-3)" (and, by the same "wrapper
    # is optional but must be technically possible" pattern,
    # ":from(:date(...))" identical to a bare date string) -- by the
    # time ReferenceFunctionFactory.build() constructs this function, a
    # nested ":index(...)"/":date(...)" arg has already been recursively
    # built into a real Index3/Date3 instance (not a plain int/str), so
    # both shapes need to be accepted here. Neither counts as a POINTER
    # for build_chain()'s "at most one pointer per chain" rule -- both
    # are nested ARGUMENTS, already unwrapped before build_chain() ever
    # sees the outer chain, exactly like ":idchain()"/":from(:index(0))"
    # nested-arg precedent noted elsewhere in this codebase's design
    # history.
    #
    NAME = "from"
    SUMMARY = (
        "The start of a range over the current scope's ordered items -- "
        "index-mode: from this 0-based position (negative counts from "
        "the end) to the end, or to :to()'s position if present. date-"
        "mode: from this calendar date onward, compared against each "
        "run's own arrival date."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (int, Index3, str, Date3)
    ARG_REQUIRED = True
