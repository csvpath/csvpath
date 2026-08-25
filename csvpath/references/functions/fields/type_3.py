from ...reference_3 import Reference3
from ..function_3 import Function3


class Type3(Function3):
    #
    # Named-File Manifest (table 1), per manifest_keys_reference_v2.md --
    # the file extension of the registered version (e.g. "csv", "xlsx").
    # Global-ledger scope (table 2's own "type") deferred alongside the
    # rest of the global-ledger batch.
    #
    NAME = "type"
    SUMMARY = "The file extension of the resolved named-file version, e.g. 'csv', 'xlsx'."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "type",
    }
    POSITIONS = {Reference3.FILES: (Reference3.NAME_THREE,)}
