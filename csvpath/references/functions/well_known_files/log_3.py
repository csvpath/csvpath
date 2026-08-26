from ...reference_3 import Reference3
from ..function_3 import Function3


class Log3(Function3):
    #
    # compendium 5.16(b) -- an outlier among the well-known-file
    # functions: it is not connected to any one datatype or entity at
    # all, just a convenience for callers (notably agents driving
    # reference expressions rather than Python) to read the project's
    # own log file without needing a separate tool/script context.
    # Must be a standalone, not-combinable name_one (no other function
    # riding alongside it, no name_two/name_three), and root_major must
    # be '*' -- see ReferenceFinder3._bare_log_call()/_query_log_call()/
    # _read_log_file() for the shared mechanism, identical across all
    # three finders.
    #
    NAME = "log"
    SUMMARY = (
        "The project's own log file (config.ini's [logging] log_file, "
        "usually logs/csvpath.log) -- the whole file as one string, or "
        "just its last N lines if an int argument is given. Standalone "
        "only, root_major must be '*'; not tied to any datatype/entity."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = (int,)
    ARG_REQUIRED = False
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_ONE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }
