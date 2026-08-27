from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedResultsName3(Function3):
    NAME = "named_results_name"
    SUMMARY = (
        "The name this run/instance's results are filed under -- same "
        "literal key at every RESULTS scope it applies to."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KIND = "name"
    KEY = {
        Reference3.RESULTS: "named_results_name",
        Reference3.RESULT: "named_results_name",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
