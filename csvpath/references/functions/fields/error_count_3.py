from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.predicate_function_3 import PredicateFunction3


class ErrorCount3(Function3):
    #
    # Results Run Manifest (table 5)'s own "error_count" -- the total
    # number of errors from every csvpath statement in the resolved
    # run, at the run-selecting (name_one) position. ALSO present at
    # the instance-selecting (name_three) position (Result Instance
    # Manifest, table 6) -- that per-instance field was missed when
    # this class was first built, confirmed 2026-10-18 directly against
    # `result_registrar.py` (the earlier comment here claiming "no
    # equivalent per-instance field... confirmed against
    # result_registrar.py" was simply wrong, same file, read more
    # carefully this time: `mdata.error_count = self.result.errors_
    # count` then `m["error_count"] = mdata.error_count`, unconditional,
    # right there). Same dual run/instance KEY shape Time3 already
    # established.
    #
    # ARG_TYPES widened 2026-10-18 (was: `()`, bare-only) --
    # normative_reference_examples.txt's own worked examples need a
    # predicate argument to GATE a pooled candidate run/instance list
    # by its own error count, not just read the number off one already-
    # selected entity:
    #   $*.results.:flatten():error_count(:above(3))   -- more than 3
    #   $*.results.:flatten():error_count(:below(1))   -- none
    #   $*.results.:flatten():error_count(0)            -- none, exact
    # A bare int (e.g. `0`) means an exact-match predicate -- no
    # dedicated predicate class needed for that case, the generic
    # dispatch (ResultsReferenceFinder3._matches_field_predicate())
    # falls back to `==` whenever the arg is not a PredicateFunction3.
    # `:above()`/`:below()` already extend PredicateFunction3 (built
    # 2026-10-17/18 respectively, for :count()'s own identical need) --
    # no change needed on their side, this is purely a consumer-side
    # widening, same declarative "any future predicate function works
    # with any existing consumer for free" pattern used throughout.
    #
    NAME = "error_count"
    SUMMARY = (
        "The number of errors from every csvpath statement in the run "
        "(name_one), or from this one csvpath statement's own instance "
        "(name_three). An optional predicate argument (e.g. "
        "':above(3)') or bare int (exact match) GATES a pooled '*'/"
        "':flatten()' candidate list by this same field, instead of "
        "just reading it off one already-selected entity."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (int, PredicateFunction3)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "error_count",
        Reference3.RESULT: "error_count",
    }
    POSITIONS = {
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }
