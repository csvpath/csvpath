from ...reference_3 import Reference3
from ..function_3 import Function3
from ..values.time_window_function_3 import TimeWindowFunction3
from .index_3 import Index3


class Before3(Function3):
    #
    # the EXCLUSIVE sibling of :to() -- compendium 6.28/6.28b/6.28c,
    # built 2026-10-16. Same two index/date modes, same shared
    # ReferenceFinder3._apply_range()/_apply_manifest_date_range()
    # mechanism as :from()/:to() (now direction-aware, see those
    # methods' own updated comments), just EXCLUSIVE of its own
    # position/date where :to() is inclusive: ":before(5)" is positions
    # 0 through 4, five items total, NOT six; ":before(:date('2025-01-
    # 31'))" excludes runs that arrived ON 2025-01-31 itself, only
    # strictly earlier ones. Aliased "below"/"lt" (6.28b's own alias
    # table) -- registered as additional ReferenceFunctionFactory
    # dict keys pointing at this same class, not separate classes; a
    # built instance's own `.name` property always reads back as
    # "before" regardless of which alias was typed (Function3.name
    # returns self.NAME, a class constant), so every downstream check
    # that branches on `.name` already sees the canonical form with no
    # extra plumbing.
    #
    # 6.28c: combining with :to() (another UPPER bound) is illegal --
    # not alike directions, nothing to narrow. May pair with :after()/
    # :from() (a LOWER bound) to form a range, same as :to() may.
    #
    # ARG_TYPES widened 2026-10-17 from Date3 specifically to
    # TimeWindowFunction3 generically (compendium 6.27) -- ":before(
    # :year())"/etc are now equally legal, using that function's own
    # start_datetime() as the exclusive upper cutoff (excludes the
    # whole period it names, same as the already-shipped day-granular
    # behavior -- see TimeWindowFunction3's own docstring for the full
    # four-way directional rule). Date3 is itself a TimeWindowFunction3
    # now, so this is strictly a widening.
    #
    NAME = "before"
    SUMMARY = (
        "The exclusive end of a range over the current scope's ordered "
        "items -- index-mode: up to but NOT including this 0-based "
        "position (negative counts from the end), from the start or "
        "from :after()'s/:from()'s position if present. date-mode: up "
        "to but not including this calendar date, compared against "
        "each run's own arrival date. Aliases: ':below()'/':lt()'."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = (int, Index3, str, TimeWindowFunction3)
    ARG_REQUIRED = True
    #
    # see From3's own POSITIONS comment -- always paired, same positions.
    #
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }
