from ...reference_3 import Reference3
from ..function_3 import Function3


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
    NAME = "error_count"
    SUMMARY = (
        "The number of errors from every csvpath statement in the run "
        "(name_one), or from this one csvpath statement's own instance "
        "(name_three)."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "error_count",
        Reference3.RESULT: "error_count",
    }
    POSITIONS = {
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }
