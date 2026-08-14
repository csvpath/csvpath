from ...reference_3 import Reference3
from ..function_3 import Function3


class Destinations3(Function3):
    #
    # see on_arrival_3.py for the definition.json-backed field-accessor
    # design this follows. Same ServerConfig shape as sources_3.py, but
    # the other direction -- where this named-paths group sends things,
    # not where a named-file is polled from. Kept as a separate name
    # from :sources() for exactly that reason, per
    # manifest_field_functions_proposal.md's Part B.
    #
    NAME = "destinations"
    SUMMARY = (
        "The destination server configurations for the resolved named-"
        "paths group, keyed by whatever name they were given -- read "
        "from definition.json. Empty if none are configured."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "definition"
    KEY = {
        Reference3.CSVPATHS: "destinations",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
