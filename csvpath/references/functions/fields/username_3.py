from ...reference_3 import Reference3
from ..function_3 import Function3


class Username3(Function3):
    NAME = "username"
    SUMMARY = "The username that executed the resolved run."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "username",
    }
