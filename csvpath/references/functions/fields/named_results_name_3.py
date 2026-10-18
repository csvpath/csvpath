from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedResultsName3(Function3):
    #
    # ARG_TYPES widened 2026-10-18 (was: `()`, bare-only) -- part of
    # compendium 6.7's "name" functional group (:named_paths_name()/
    # :named_results_name()/:named_file_name()), the same retrieve/
    # select duality rule as the already-widened "uuid" group. An
    # argument GATES a pooled RESULTS candidate list by this field --
    # same generic field_call/_matches_field_predicate mechanism
    # :error_count()/:named_file_name()/:uuid() already use, no finder-
    # side code needed.
    #
    NAME = "named_results_name"
    SUMMARY = (
        "The name this run/instance's results are filed under -- same "
        "literal key at every RESULTS scope it applies to. An optional "
        "string argument GATES a pooled candidate list by this field."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KIND = "name"
    KEY = {
        Reference3.RESULTS: "named_results_name",
        Reference3.RESULT: "named_results_name",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
