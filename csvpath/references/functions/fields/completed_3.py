from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.predicate_function_3 import PredicateFunction3


class Completed3(Function3):
    #
    # aggregate/individual pair, same shape as valid_3.py: run scope has
    # no field literally called "completed" -- it has "all_completed",
    # an aggregate across every statement in the run. Instance scope has
    # "completed", this one statement's own completion state.
    #
    NAME = "completed"
    SUMMARY = (
        "Run scope: true if every csvpath statement in the run reports "
        "completed. Instance scope: true if this one statement reports "
        "completed."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    ARG_TYPES = (PredicateFunction3,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "all_completed",
        Reference3.RESULT: "completed",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
