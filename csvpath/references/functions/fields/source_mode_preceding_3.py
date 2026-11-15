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
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULT: "source_mode_preceding",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}
