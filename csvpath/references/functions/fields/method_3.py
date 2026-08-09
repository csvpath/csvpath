from ...reference_3 import Reference3
from ..function_3 import Function3


class Method3(Function3):
    NAME = "method"
    SUMMARY = "The run method used for the resolved run (e.g. collect, fast_forward)."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "method",
    }
