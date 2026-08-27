from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedFilePath3(Function3):
    #
    # Results Run Manifest (table 5)'s own "named_file_path" -- the
    # path to the named-file version used as this run's data input.
    # Deliberately distinct from FilePath3/:file_path() (the FILES
    # datatype's own version path) -- this is RESULTS' own record of
    # which file it consumed, not a FILES-side field.
    #
    NAME = "named_file_path"
    SUMMARY = "The path to the named-file version used as input to the resolved run."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "named_file_path",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
