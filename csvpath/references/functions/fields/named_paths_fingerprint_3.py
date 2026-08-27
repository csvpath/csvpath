from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedPathsFingerprint3(Function3):
    #
    # Results Run Manifest (table 5)'s own "named_paths_fingerprint" --
    # the fingerprint of the named-paths group version whose content
    # drove this run. A different ENTITY's content than Fingerprint3/
    # :fingerprint() (the FILES/CSVPATHS entity's own content
    # fingerprint) describes, but the same conceptual KIND -- see
    # fingerprint_3.py's own note on why these are grouped for UNION
    # comparison purposes (byte-identity) despite belonging to
    # different entities. Lets a run be compared, by content (not
    # registration event), against the named-paths group that produced
    # it -- catching the case where the same group.csvpaths text was
    # loaded under two different names (different uuids, identical
    # fingerprints), something named_paths_uuid/:named_paths_uuid()
    # cannot do.
    #
    NAME = "named_paths_fingerprint"
    SUMMARY = (
        "The fingerprint of the named-paths group version whose content "
        "drove the resolved run."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KIND = "fingerprint"
    KEY = {
        Reference3.RESULTS: "named_paths_fingerprint",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
