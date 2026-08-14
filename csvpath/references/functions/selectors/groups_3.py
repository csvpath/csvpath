from ...reference_3 import Reference3
from ..function_3 import Function3


class Groups3(Function3):
    #
    # the any-depth GROUP peer of ':flatten()' (any-depth POOL) --
    # completes the 2x2 depth matrix alongside '*'/':all()' (both
    # restricted to exactly one level): '*'/':flatten()' pool into one
    # answer, ':all()'/':groups()' partition into one answer per
    # distinct value. Added 2026-08-12, together with FILES/RESULTS
    # both getting it in the same pass -- David's own principle (see
    # feedback_cross_datatype_function_consistency): keep functions
    # meaning the same thing across datatypes wherever the underlying
    # structure supports it. Deliberately deferred through the whole
    # ':all()'/':flatten()' work leading up to this -- David judged it
    # no longer deferrable once a concrete need surfaced for FILES (a
    # named-file's distinct paths are not always uniformly one level
    # deep) and confirmed RESULTS should get it in the same pass rather
    # than drift out of sync again the way ':all()' already had once.
    #
    # CSVPATHS has no path dimension at all to group by, so it is
    # excluded here -- same reasoning that already excludes it from
    # ':flatten()'.
    #
    NAME = "groups"
    SUMMARY = (
        "Partitions every match at this position, at any remaining "
        "depth, by its own distinguishing path, reducing each "
        "partition independently by a pointer riding alongside it -- "
        "the any-depth counterpart to ':all()', which is restricted to "
        "exactly one level."
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
