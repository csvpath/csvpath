from ...reference_3 import Reference3
from ..function_3 import Function3


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
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.CSVPATHS: "named_paths",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
