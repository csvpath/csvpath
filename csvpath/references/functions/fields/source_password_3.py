from ...reference_3 import Reference3
from ..function_3 import Function3


class SourcePassword3(Function3):
    #
    # see source_address_3.py for the shared arg-keyed design this
    # follows.
    #
    NAME = "source_password"
    SUMMARY = (
        "The login password of the named source entry (by name) for "
        "the resolved named-file, read from definition.json's "
        "sources.<name>.password. Requires a source name argument."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = True
    SOURCE = "definition"
    KEY = {
        Reference3.FILES: "sources.{}.password",
    }
    POSITIONS = {Reference3.FILES: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
