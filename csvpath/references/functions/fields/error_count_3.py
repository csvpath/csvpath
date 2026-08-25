from ...reference_3 import Reference3
from ..function_3 import Function3


class ErrorCount3(Function3):
    #
    # Results Run Manifest (table 5)'s own "error_count" -- the total
    # number of errors from every csvpath statement in the run. Run
    # scope only -- no equivalent per-instance field in the Result
    # Instance Manifest (table 6), confirmed against result_registrar.py.
    #
    NAME = "error_count"
    SUMMARY = "The total number of errors from every csvpath statement in the resolved run."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "error_count",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
