from ...reference_3 import Reference3
from ..function_3 import Function3


class Uuid3(Function3):
    #
    # first of the shared, context-dispatching field-accessor functions
    # (see references_notes/notes/manifest_field_functions_proposal.md,
    # Part A) -- reads the "uuid" key straight off the manifest entry a
    # pointer (or the absence of one) already resolved, exactly the way
    # :manifest() itself rides alongside a pointer, except this pulls one
    # field out instead of handing back the whole entry. RESULTS scope
    # (run/instance) is deliberately not wired in yet -- that needs the
    # run/instance scope-dispatch mechanism the proposal doc flags as a
    # prerequisite, not yet built.
    #
    NAME = "uuid"
    SUMMARY = (
        "The uuid of the resolved named-file/named-paths version -- the "
        "registration/load event's own identifier, read straight off its "
        "manifest entry."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "uuid",
        Reference3.CSVPATHS: "uuid",
    }
