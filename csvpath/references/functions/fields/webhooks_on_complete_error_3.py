from ...reference_3 import Reference3
from ..function_3 import Function3


class WebhooksOnCompleteError3(Function3):
    #
    # see webhooks_on_complete_all_3.py for the shared four-fixed-field
    # design this follows (no argument -- not keyed by any name).
    #
    NAME = "webhooks_on_complete_error"
    SUMMARY = (
        "The completion webhook (url/payload/headers) configured to "
        "fire only when the csvpath statement has errors, for the "
        "resolved named-paths group -- read from definition.json's "
        "webhooks.on_complete_error. None if not configured."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "definition"
    KEY = {
        Reference3.CSVPATHS: "webhooks.on_complete_error",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
