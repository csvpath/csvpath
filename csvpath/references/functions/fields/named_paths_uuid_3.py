from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedPathsUuid3(Function3):
    #
    # the uuid of the named-paths group VERSION that drove a run --
    # present at both run scope (table 5) and instance scope (table 6),
    # same literal key at both.
    #
    NAME = "named_paths_uuid"
    SUMMARY = (
        "The uuid of the named-paths group version that produced the "
        "resolved run or instance."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "named_paths_uuid",
        Reference3.RESULT: "named_paths_uuid",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
