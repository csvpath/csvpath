from ...reference_3 import Reference3
from ..function_3 import Function3


class Hostname3(Function3):
    NAME = "hostname"
    SUMMARY = "The hostname of the machine that executed the resolved run."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "hostname",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
