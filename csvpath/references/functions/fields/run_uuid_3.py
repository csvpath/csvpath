from ...reference_3 import Reference3
from ..function_3 import Function3


class RunUuid3(Function3):
    #
    # first field accessor targeting RESULTS -- see uuid_3.py for the
    # scope-dependent counter-case. "run_uuid" is the same literal key at
    # run scope (table 5) and instance scope (table 6), so both KEY
    # entries hold the identical value -- kept as two entries anyway
    # (not one, with the finder falling back) so the finder's own
    # dispatch stays uniform: always look up whichever constant matches
    # where this rode (Reference3.RESULTS for name_one, Reference3.RESULT
    # for name_three), never a special case for "this one happens to be
    # the same either way." Distinct from :uuid(), which DOES vary by
    # scope (and is instance-only) -- "which run does this belong to"
    # vs. "this entity's own id" only coincide below run scope.
    #
    NAME = "run_uuid"
    SUMMARY = (
        "The uuid of the run the resolved run or instance belongs to -- "
        "same literal key at every RESULTS scope it applies to."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "run_uuid",
        Reference3.RESULT: "run_uuid",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
