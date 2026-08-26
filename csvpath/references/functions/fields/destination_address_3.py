from ...reference_3 import Reference3
from ..function_3 import Function3


class DestinationAddress3(Function3):
    #
    # destinations_3.py's own "destinations" object IS keyed by an
    # arbitrary destination name (confirmed against paths_descriptor.
    # py's GroupConfig.destinations: dict[str, ServerConfig]) -- same
    # arg-keyed shape as sources_3.py's own fields (see
    # source_address_3.py), just the other direction.
    #
    NAME = "destination_address"
    SUMMARY = (
        "The hostname or IP address of the named destination entry "
        "(by name) for the resolved named-paths group, read from "
        "definition.json's destinations.<name>.address. Requires a "
        "destination name argument."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = True
    SOURCE = "definition"
    KEY = {
        Reference3.CSVPATHS: "destinations.{}.address",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
