from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedPathsName3(Function3):
    #
    # CSVPATHS self-reference (this group's own registered name, read
    # off its own manifest) plus RESULTS run scope (which named-paths
    # group the run belongs to). Not instance scope -- the Result
    # Instance Manifest does not carry this field, confirmed against
    # result_registrar.py's metadata_update().
    #
    NAME = "named_paths_name"
    SUMMARY = (
        "The name of the resolved named-paths group -- its own name for "
        "CSVPATHS, or the run's named-paths group for RESULTS run "
        "scope."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.CSVPATHS: "named_paths_name",
        Reference3.RESULTS: "named_paths_name",
    }
    POSITIONS = {
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        # RESULTS: KEY only has a RESULTS entry, no RESULT (instance)
        # entry -- run scope only.
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }
