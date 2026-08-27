from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedFileLastChange3(Function3):
    #
    # Results Run Manifest (table 5)'s own "named_file_last_change" --
    # the last-modified timestamp of the named-file version used, read
    # from the filesystem at the moment the run started. Falls back to
    # -1 if the file cannot be found, per results_registrar.py.
    #
    NAME = "named_file_last_change"
    SUMMARY = (
        "The last-modified timestamp of the named-file version used as "
        "input to the resolved run."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "named_file_last_change",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
