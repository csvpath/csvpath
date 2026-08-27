from ...reference_3 import Reference3
from ..function_3 import Function3


class InstanceHome3(Function3):
    #
    # split out of :home() (2026-08-26, see :home()'s own docstring and
    # the "split :home()'s field-read job" bucket-list entry) -- reads
    # the "instance_home" key off whatever instance a name_three
    # identity/:all() already selected. Instance scope only -- see
    # :run_home() for the run-scope half. Dispatched via
    # ResultsReferenceFinder3._extract_data()'s own name_three field_call
    # branch, which always reads Function3.KEY[Reference3.RESULT] (the
    # instance-scope key, only ever consulted there, never a real value
    # of Reference3.datatype), so this only needs (and only declares)
    # that one key.
    #
    NAME = "instance_home"
    SUMMARY = "The path to the resolved instance's own home directory."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULT: "instance_home",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}
