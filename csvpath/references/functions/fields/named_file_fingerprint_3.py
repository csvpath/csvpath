from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedFileFingerprint3(Function3):
    #
    # Results Run Manifest (table 5)'s own "named_file_fingerprint" --
    # the fingerprint of the named-file version used as this run's data
    # input. A different ENTITY's content than Fingerprint3/
    # :fingerprint() (the FILES/CSVPATHS entity's own content
    # fingerprint) describes, but the same conceptual KIND -- see
    # fingerprint_3.py's own note on why these are grouped for UNION
    # comparison purposes (byte-identity) despite belonging to
    # different entities.
    #
    NAME = "named_file_fingerprint"
    SUMMARY = "The fingerprint of the named-file version used as input to the resolved run."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KIND = "fingerprint"
    KEY = {
        Reference3.RESULTS: "named_file_fingerprint",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
