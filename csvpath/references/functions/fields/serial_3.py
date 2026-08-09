from ...reference_3 import Reference3
from ..function_3 import Function3


class Serial3(Function3):
    #
    # see run_uuid_3.py for why both KEY entries hold the identical
    # value -- "serial" is the same literal key at run scope (table 5)
    # and instance scope (table 6), but the finder's dispatch always
    # looks up the constant matching where this rode, so both need an
    # entry regardless of the value being the same.
    #
    NAME = "serial"
    SUMMARY = (
        "True if the run completes csvpath statements serially, rather "
        "than completing a pass through all of them as each line is "
        "processed -- same literal key at every RESULTS scope it "
        "applies to."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "serial",
        Reference3.RESULT: "serial",
    }
