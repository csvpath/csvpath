from ...reference_3 import Reference3
from ..function_3 import Function3


class Sources3(Function3):
    #
    # see on_arrival_3.py for the definition.json-backed field-accessor
    # design this follows.
    #
    NAME = "sources"
    SUMMARY = (
        "The remote source server configurations for the resolved named-"
        "file, keyed by whatever name they were given -- read from "
        "definition.json. Empty if none are configured."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "definition"
    KEY = {
        Reference3.FILES: "sources",
    }
    #
    # BOTH positions -- see on_arrival_3.py's own POSITIONS comment.
    #
    POSITIONS = {Reference3.FILES: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
