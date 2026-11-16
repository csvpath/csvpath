from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.does_not_have_value_3 import DoesNotHaveValue3
from ..filters.has_value_3 import HasValue3


class NamedPaths3(Function3):
    #
    # Named-Paths Manifest (table 3)'s own "named_paths" -- the
    # complete, verbatim text of every csvpath statement comprising
    # this version of the named-paths group. Can be a large value --
    # no special handling here, resolved the same as any other field.
    #
    NAME = "named_paths"
    SUMMARY = (
        "The complete, byte-for-byte text of every csvpath statement "
        "in the resolved version of this named-paths group."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    # a collection: only the value predicates filter it -- an equality
    # test on a list or dict means nothing (RC triage B5, David
    # 2026-11-16; compendium 6.40)
    ARG_TYPES = (HasValue3, DoesNotHaveValue3)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.CSVPATHS: "named_paths",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
