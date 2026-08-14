from ...reference_3 import Reference3
from ..function_3 import Function3


class Valid3(Function3):
    #
    # the genuinely scope-divergent case Reference3.RESULT exists for:
    # run scope (table 5) has no field literally called "valid" -- it
    # has "all_valid", an aggregate across every statement in the run,
    # written only once the run completes (optional -- absent for an
    # in-progress run, which _extract_field_value's own tolerance for a
    # missing key already handles as None, not an error). Instance scope
    # (table 6) has "valid", this one statement's own validity. An
    # aggregate and an individual are different questions, so one shared
    # function name reading two different manifest keys by scope is the
    # right shape here -- settled 2026-08-09, not revisiting.
    #
    NAME = "valid"
    SUMMARY = (
        "Run scope: true if every csvpath statement in the run reports "
        "valid (none failed via fail() or a validation-mode of fail). "
        "Instance scope: true if this one statement reports valid."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "all_valid",
        Reference3.RESULT: "valid",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
