from ...reference_3 import Reference3
from ..function_3 import Function3


class InstanceIndex3(Function3):
    #
    # Result Instance Manifest (table 6)'s own "instance_index" -- the
    # 0-based index of this csvpath statement within the named-paths
    # group, distinct from Identity3/:identity() (the statement's own
    # name, or that same index stringified when unnamed).
    #
    NAME = "instance_index"
    SUMMARY = "The 0-based index of the resolved csvpath-statement instance within its named-paths group."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULT: "instance_index",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}
