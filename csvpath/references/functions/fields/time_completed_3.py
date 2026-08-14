from ...reference_3 import Reference3
from ..function_3 import Function3


class TimeCompleted3(Function3):
    #
    # not applicable to FILES -- table 1 has no equivalent (a version
    # registration has no separate "completed" moment). Same literal
    # key at both scopes it does apply to. RESULTS instance scope is
    # deliberately excluded -- the Result Instance Manifest has no
    # "time_completed" field (confirmed against result_registrar.py).
    #
    NAME = "time_completed"
    SUMMARY = (
        "The moment the resolved named-paths load, or results run, "
        "finished -- absent (None) while still in progress."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.CSVPATHS: "time_completed",
        Reference3.RESULTS: "time_completed",
    }
    POSITIONS = {
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        # RESULTS: KEY only has a RESULTS entry, no RESULT (instance)
        # entry -- run scope only (matches the class's own docstring:
        # "RESULTS instance scope is deliberately excluded").
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }
