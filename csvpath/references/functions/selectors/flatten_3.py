from ...reference_3 import Reference3
from ..function_3 import Function3


class Flatten3(Function3):
    #
    # Originally RESULTS-only. Settled 2026-08-10, alongside redefining
    # a bare pointer to mean zero-level-only (see
    # ResultsReferenceFinder3's module docstring and
    # _query_star_traversal). Once bare stopped meaning "any depth,
    # pooled," that capability needed a new, explicit name -- :flatten()
    # is it. Unlike "*"/:all() (which are depth PEERS, both requiring
    # exactly one level), :flatten() pools every match at its own
    # position (bare, or after a literal prefix) at ANY remaining depth
    # into one combined list, the same way a bare pointer used to. A
    # deferred peer, :groups(), would do the same any-depth matching but
    # partition instead of pool -- both finders keep candidate-gathering
    # and pool-vs-reduce as separate steps specifically so that peer is
    # a small addition later, not a rework, when/if it is needed.
    #
    # Extended to FILES 2026-08-12: FILES also has variable, unknown-in-
    # advance path depth (a named-file's distinct files need not all sit
    # at the same depth), the same structural reason RESULTS needed this
    # -- David's own principle: keep functions meaning the same thing
    # across datatypes wherever the underlying structure supports it.
    # CSVPATHS has no path dimension at all, so it stays excluded, same
    # as :all()'s own grouping is a no-op there.
    #
    NAME = "flatten"
    SUMMARY = (
        "Pools every match at this position at any remaining depth into "
        "one combined list, reduced by a pointer riding alongside it -- "
        "the any-depth counterpart to '*'/':all()', which are both "
        "restricted to exactly one level."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.FILES, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    #
    # RESULTS entry deferred until that Finder is retrofitted to enforce
    # POSITIONS the same way (see Function3.POSITIONS's own docstring).
    #
    POSITIONS = {Reference3.FILES: (Reference3.NAME_ONE,)}
