from ...reference_3 import Reference3
from ..function_3 import Function3


class Method3(Function3):
    NAME = "method"
    SUMMARY = "The run method used for the resolved run (e.g. collect, fast_forward)."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "method",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
