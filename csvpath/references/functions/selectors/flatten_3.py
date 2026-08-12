from ...reference_3 import Reference3
from ..function_3 import Function3


class Flatten3(Function3):
    #
    # RESULTS-only. Settled 2026-08-10, alongside redefining a bare
    # pointer to mean zero-level-only (see ResultsReferenceFinder3's
    # module docstring and _query_star_traversal). Once bare stopped
    # meaning "any depth, pooled," that capability needed a new,
    # explicit name -- :flatten() is it. Unlike "*"/:all() (which are
    # depth PEERS, both requiring exactly one level), :flatten() pools
    # every run matching its own position (bare, or after a literal
    # prefix) at ANY remaining depth into one combined list, the same
    # way a bare pointer used to. A deferred peer, :groups(), would do
    # the same any-depth matching but partition instead of pool --
    # ResultsReferenceFinder3 keeps candidate-gathering and pool-vs-
    # reduce as separate steps specifically so that peer is a small
    # addition later, not a rework, when/if it is needed.
    #
    NAME = "flatten"
    SUMMARY = (
        "Pools every run matching this position at any remaining depth "
        "into one combined list, reduced by a pointer riding alongside "
        "it -- the any-depth counterpart to '*'/':all()', which are "
        "both restricted to exactly one level."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
