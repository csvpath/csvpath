from ...reference_3 import Reference3
from ..function_3 import Function3


class SourceAddress3(Function3):
    #
    # sources_3.py's own "sources" object IS keyed by an arbitrary
    # source name (confirmed against file_descriptor.py's Config.
    # sources: dict[str, ServerConfig]) -- unlike scripts/webhooks,
    # this genuinely needs an argument to say which named source entry
    # to read. KEY holds a "{}" placeholder, filled with this call's
    # own arg by ReferenceFinder3._apply_key_arg() before the ordinary
    # dotted-path walk (added 2026-08-26 -- the first field accessors
    # needing this; see that method's own docstring).
    #
    NAME = "source_address"
    SUMMARY = (
        "The hostname or IP address of the named source entry (by "
        "name) for the resolved named-file, read from definition.json's "
        "sources.<name>.address. Requires a source name argument."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = True
    SOURCE = "definition"
    KEY = {
        Reference3.FILES: "sources.{}.address",
    }
    POSITIONS = {Reference3.FILES: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
