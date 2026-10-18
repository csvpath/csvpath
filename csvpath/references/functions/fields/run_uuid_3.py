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
    # ARG_TYPES widened 2026-10-18 (was: `()`, bare-only) -- normative_
    # reference_examples.txt's own worked examples ("$*.results.
    # :manifest():run_uuid(\"789a...\"):template()", "$*.results.
    # :flatten():run_uuid(\"789a...\"):template()") need a string
    # argument to GATE a pooled/manifest-read RESULTS candidate list by
    # this field -- the exact same generic field_call/_matches_field_
    # predicate mechanism :error_count()/:uuid() use, confirmed live,
    # no finder-side code needed. NOT also SELECTOR_WHEN_ARGUED -- this
    # function has no FILES/CSVPATHS bare-lookup shape at all (RESULTS-
    # only, unlike :uuid()), so there is no "entity" for a bare form to
    # select here.
    #
    NAME = "run_uuid"
    SUMMARY = (
        "The uuid of the run the resolved run or instance belongs to -- "
        "same literal key at every RESULTS scope it applies to. An "
        "optional string argument GATES a pooled/manifest-read "
        "candidate list by this field."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KIND = "uuid"
    KEY = {
        Reference3.RESULTS: "run_uuid",
        Reference3.RESULT: "run_uuid",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
