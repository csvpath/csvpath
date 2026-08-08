from ...reference_3 import Reference3
from ..function_3 import Function3


class Last3(Function3):
    NAME = "last"
    SUMMARY = "The most-recently-arriving item in the current scope."
    ROLE = Function3.POINTER
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
