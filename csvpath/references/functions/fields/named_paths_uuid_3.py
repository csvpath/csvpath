from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedPathsUuid3(Function3):
    #
    # the uuid of the named-paths group VERSION that drove a run --
    # present at both run scope (table 5) and instance scope (table 6),
    # same literal key at both.
    #
    # ARG_TYPES widened 2026-10-18 (was: `()`, bare-only) -- part of
    # compendium 6.7's "uuid" functional group (:uuid()/:run_uuid()/
    # :named_file_uuid()/:named_paths_uuid()), the same retrieve/select
    # duality rule already built for the other two members. An
    # argument GATES a pooled RESULTS candidate list by this field --
    # same generic field_call/_matches_field_predicate mechanism
    # :error_count()/:uuid() already use, no finder-side code needed.
    #
    NAME = "named_paths_uuid"
    SUMMARY = (
        "The uuid of the named-paths group version that produced the "
        "resolved run or instance. An optional string argument GATES "
        "a pooled candidate list by this field."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KIND = "uuid"
    KEY = {
        Reference3.RESULTS: "named_paths_uuid",
        Reference3.RESULT: "named_paths_uuid",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
