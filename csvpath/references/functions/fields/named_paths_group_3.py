from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedPathsGroup3(Function3):
    #
    # Named-File Definition (table 8)'s own "on_arrival.named_paths_group"
    # -- see on_arrival_3.py for the shared definition.json-backed
    # design this follows (SOURCE == "definition", both bare/name_one
    # and name_three positions legal, no result.uuid needed since
    # definition.json is not versioned). Dotted KEY path, walked by the
    # shared _extract_field_value() helper.
    #
    NAME = "named_paths_group"
    SUMMARY = (
        "The named-paths group configured to run automatically when "
        "the resolved named-file receives a new version, from "
        "definition.json's on_arrival config."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "definition"
    KEY = {
        Reference3.FILES: "on_arrival.named_paths_group",
    }
    POSITIONS = {Reference3.FILES: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
