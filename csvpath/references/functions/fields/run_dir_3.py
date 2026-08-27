from ...reference_3 import Reference3
from ..function_3 import Function3


class RunDir3(Function3):
    #
    # Result Instance Manifest (table 6)'s own "run" key -- the run dir
    # name (a timestamp, disambiguated if needed). Named RunDir3/
    # :run_dir() rather than :run(), matching the manifest doc's own
    # note that "run_dir" is the commonly used name for this, not "run".
    #
    NAME = "run_dir"
    SUMMARY = "The run directory name (timestamp, disambiguated if needed) of the resolved instance's own run."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULT: "run",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}
