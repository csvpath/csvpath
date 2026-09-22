from ...reference_3 import Reference3
from ..function_3 import Function3


class TimeCompleted3(Function3):
    #
    # not applicable to FILES -- table 1 has no equivalent (a version
    # registration has no separate "completed" moment). RESULTS instance
    # scope is also excluded -- the Result Instance Manifest has no
    # "time_completed" field (confirmed against result_registrar.py).
    #
    # CSVPATHS removed 2026-09-21 (David: "csvpaths time_completed is
    # next to useless and shouldn't exist" -- a load's completion moment
    # is not a meaningful thing to expose; table 3's own field is
    # documented N/A). Was DATATYPES = (CSVPATHS, RESULTS), KEY had a
    # CSVPATHS entry ("time_completed"), POSITIONS had a CSVPATHS entry
    # (NAME_ONE,) -- all removed together.
    #
    NAME = "time_completed"
    SUMMARY = (
        "The moment the resolved results run finished -- absent (None) "
        "while still in progress."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "time_completed",
    }
    POSITIONS = {
        # KEY only has a RESULTS entry, no RESULT (instance) entry --
        # run scope only (matches the class's own docstring: "RESULTS
        # instance scope is also excluded").
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }
