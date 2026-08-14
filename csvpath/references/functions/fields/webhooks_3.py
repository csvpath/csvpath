from ...reference_3 import Reference3
from ..function_3 import Function3


class Webhooks3(Function3):
    #
    # see on_arrival_3.py for the definition.json-backed field-accessor
    # design this follows, and scripts_3.py for the shared four-state
    # (on_complete_all/valid/invalid/error) convention.
    #
    NAME = "webhooks"
    SUMMARY = (
        "The completion webhooks configured for the resolved named-paths "
        "group -- on_complete_all/valid/invalid/error, each a "
        "url/payload/headers object -- read from definition.json. Empty "
        "if none are configured."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "definition"
    KEY = {
        Reference3.CSVPATHS: "webhooks",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
