from ...reference_3 import Reference3
from ..function_3 import Function3


class First3(Function3):
    NAME = "first"
    SUMMARY = "The earliest-arriving item in the current scope."
    ROLE = Function3.POINTER
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        # RESULTS: name_one only -- name_three has no pointer concept of
        # its own (_name_three_selector recognizes a literal identity,
        # :all(), or ':from()'/':to()', never a pointer).
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }
