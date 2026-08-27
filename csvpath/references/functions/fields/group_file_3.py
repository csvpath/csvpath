from ...reference_3 import Reference3
from ..function_3 import Function3


class GroupFile3(Function3):
    #
    # Named-Paths Manifest (table 3)'s own "group_file_path" -- the
    # path to this named-paths group's group.csvpaths file. Table 4's
    # own copy of this field (the global loads ledger) is deferred
    # alongside the rest of the global-ledger batch.
    #
    NAME = "group_file"
    SUMMARY = "The path to the resolved named-paths group's group.csvpaths file."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.CSVPATHS: "group_file_path",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
