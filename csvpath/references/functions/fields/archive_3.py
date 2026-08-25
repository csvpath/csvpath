from ...reference_3 import Reference3
from ..function_3 import Function3


class Archive3(Function3):
    #
    # Named-Paths Manifest (table 3)'s "archive_name" (the configured
    # [results] archive value at load time) and the Result Instance
    # Manifest (table 6)'s own "archive_name" (the archive dir name at
    # the time this result was generated) -- same literal key, same
    # concept (a snapshot of the archive dir name at some past moment),
    # different entities. RESULTS run scope (table 5) has no equivalent
    # field -- confirmed against results_registrar.py, not assumed.
    #
    NAME = "archive"
    SUMMARY = (
        "The archive directory name in effect at the moment the "
        "resolved entity was created -- the named-paths group's own "
        "load-time snapshot, or a result instance's own."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.CSVPATHS: "archive_name",
        Reference3.RESULT: "archive_name",
    }
    POSITIONS = {
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        Reference3.RESULTS: (Reference3.NAME_THREE,),
    }
