from ...reference_3 import Reference3
from ..function_3 import Function3


class Scripts3(Function3):
    #
    # see on_arrival_3.py for the definition.json-backed field-accessor
    # design this follows. CSVPATHS side of the same on_complete_all/
    # on_complete_valid/on_complete_invalid/on_complete_error convention
    # webhooks_3.py and transfers_3.py also use.
    #
    NAME = "scripts"
    SUMMARY = (
        "The completion scripts configured for the resolved named-paths "
        "group -- on_complete_all/valid/invalid/error, each a script "
        "filename -- read from definition.json. Empty if none are "
        "configured."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "definition"
    KEY = {
        Reference3.CSVPATHS: "scripts",
    }
