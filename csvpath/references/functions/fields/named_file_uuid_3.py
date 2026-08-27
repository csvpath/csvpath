from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedFileUuid3(Function3):
    #
    # Results Run Manifest (table 5)'s own "named_file_uuid" -- the uuid
    # of the named-file version used as this run's data input. Run scope
    # only -- confirmed no equivalent field in the Result Instance
    # Manifest (table 6).
    #
    NAME = "named_file_uuid"
    SUMMARY = "The uuid of the named-file version used as input to the resolved run."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KIND = "uuid"
    KEY = {
        Reference3.RESULTS: "named_file_uuid",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
