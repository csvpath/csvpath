from ...reference_3 import Reference3
from ..function_3 import Function3


class RunHome3(Function3):
    #
    # split out of :home() (2026-08-26, see :home()'s own docstring and
    # the "split :home()'s field-read job" bucket-list entry) -- reads
    # the "run_home" key off whatever run a pointer already selected.
    # Run scope only -- deliberately does NOT also serve instance scope
    # the way :home() used to (see :instance_home() for that half); a
    # name_one-riding field accessor here is dispatched via
    # ResultsReferenceFinder3._extract_data()'s own run_field_call
    # branch, which always reads Function3.KEY[Reference3.RESULTS] and
    # explicitly rejects a name_three alongside it, so this only needs
    # (and only declares) that one key.
    #
    NAME = "run_home"
    SUMMARY = "The path to the resolved run's own home directory."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "run_home",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
