from ...reference_3 import Reference3
from ..function_3 import Function3
from .index_3 import Index3


class From3(Function3):
    #
    # index-mode range selector -- added 2026-08-13, RESULTS only for
    # now (the doc's own confirmed examples are all RESULTS; FILES/
    # CSVPATHS get this later if a concrete need shows up, per this
    # session's own "build only what's confirmed" discipline). Packaged
    # together with :to() on purpose (David: "our version of BETWEEN in
    # SQL or range() in Python... I'd only separate them if there is
    # some underlying implementation detail that makes them better
    # tackled as two things" -- there isn't; both slice an already-
    # ordered candidate list, :from() sets the start bound, :to() the
    # end bound, see ReferenceFinder3._range_bound()).
    #
    # ARG_TYPES includes Index3, not just int, because the doc's own
    # NOTES block explicitly requires ":from(:index(-3))" to be legal
    # and identical to ":from(-3)" -- by the time ReferenceFunctionFactory
    # .build() constructs this function, a nested ":index(...)" arg has
    # already been recursively built into a real Index3 instance (not a
    # plain int), so both shapes need to be accepted here. Does not
    # count as a POINTER for build_chain()'s "at most one pointer per
    # chain" rule -- it is a nested ARGUMENT, already unwrapped before
    # build_chain() ever sees the outer chain, exactly like
    # ":idchain()"/":from(:index(0))" nested-arg precedent noted
    # elsewhere in this codebase's design history.
    #
    NAME = "from"
    SUMMARY = (
        "The start of an index-based range over the current scope's "
        "ordered items -- from this 0-based position (negative counts "
        "from the end) to the end, or to :to()'s position if present."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (int, Index3)
    ARG_REQUIRED = True
