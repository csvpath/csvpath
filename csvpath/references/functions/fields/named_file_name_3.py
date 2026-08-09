from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedFileName3(Function3):
    NAME = "named_file_name"
    SUMMARY = (
        "The name of the named-file this run/instance consumed as its "
        "input -- same literal key at every RESULTS scope it applies "
        "to."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "named_file_name",
        Reference3.RESULT: "named_file_name",
    }
