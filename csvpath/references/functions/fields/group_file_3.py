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
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.CSVPATHS: "group_file_path",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
