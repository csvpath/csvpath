from ...reference_3 import Reference3
from ..function_3 import Function3


class DestinationPassword3(Function3):
    #
    # see destination_address_3.py for the shared arg-keyed design
    # this follows.
    #
    NAME = "destination_password"
    SUMMARY = (
        "The login password of the named destination entry (by name) "
        "for the resolved named-paths group, read from definition."
        "json's destinations.<name>.password. Requires a destination "
        "name argument."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = True
    SOURCE = "definition"
    KEY = {
        Reference3.CSVPATHS: "destinations.{}.password",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
