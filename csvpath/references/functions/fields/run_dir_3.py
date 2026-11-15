from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.does_not_have_value_3 import DoesNotHaveValue3
from ..filters.has_value_3 import HasValue3


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
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    # and :has_value()/:does_not_have_value(): "Every field matches exactly
    # one of the two" (NRE); other predicates on a string are not ruled
    ARG_TYPES = (str, HasValue3, DoesNotHaveValue3)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULT: "run",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}
