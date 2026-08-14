from ...reference_3 import Reference3
from ..function_3 import Function3


class Status3(Function3):
    #
    # run scope only -- a lifecycle marker ("started"/"complete"), not
    # to be confused with the FILES ledger's own "status" (a failure
    # message, unexposed today) -- different concept, same literal key,
    # per manifest_field_functions_proposal.md's Part B note on this
    # function.
    #
    NAME = "status"
    SUMMARY = (
        "The lifecycle status of the resolved run -- 'started' or "
        "'complete'."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "status",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
