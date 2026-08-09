from ...reference_3 import Reference3
from ..function_3 import Function3


class Identity3(Function3):
    #
    # instance scope only -- a run has no single "identity" of its own,
    # it is a collection of instances, each with its own. No
    # Reference3.RESULTS entry, same pattern as uuid_3.py at run scope.
    #
    NAME = "identity"
    SUMMARY = (
        "The csvpath-statement identity of the resolved instance -- "
        "explicit :id/:name metadata, or the stringified load-time "
        "index for an unnamed statement."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULT: "instance_identity",
    }
