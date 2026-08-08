from ...reference_3 import Reference3
from ..function_3 import Function3


class OnArrival3(Function3):
    #
    # first of the definition.json-backed field accessors -- SOURCE is
    # "definition", not "manifest", so a finder resolves this against
    # the enclosing named-file's definition.json config instead of a
    # manifest entry, and does not need result.uuid to do it:
    # definition.json is not versioned (see Definition3), so there is
    # only ever one on_arrival value regardless of which version a
    # reference otherwise narrowed to. Almost certainly the function
    # David originally had in mind calling ":activation()" -- see
    # manifest_field_functions_proposal.md's Part B.
    #
    NAME = "on_arrival"
    SUMMARY = (
        "The on_arrival configuration for the resolved named-file -- "
        "which named-paths group and run method to trigger automatically "
        "when a new version arrives, read from definition.json. None if "
        "the named-file was never configured for this."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "definition"
    KEY = {
        Reference3.FILES: "on_arrival",
    }
