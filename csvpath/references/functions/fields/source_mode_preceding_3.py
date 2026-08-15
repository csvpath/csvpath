from ...reference_3 import Reference3
from ..function_3 import Function3


class SourceModePreceding3(Function3):
    NAME = "source_mode_preceding"
    SUMMARY = (
        "True if this instance's actual data file is the preceding "
        "instance's data.csv, rather than the named-file directly."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULT: "source_mode_preceding",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}
