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
    # ARG_TYPES widened 2026-10-18 (was: `()`, bare-only) -- not
    # directly cited with an argument in the normative doc, but this
    # class already declares KIND="fingerprint" (compendium 6.7's
    # "fingerprint" functional group, alongside :fingerprint()/:named_
    # file_fingerprint()), the same retrieve/select duality rule
    # already built for its two siblings. An argument GATES a pooled
    # RESULTS candidate list by this field -- same generic field_call/
    # _matches_field_predicate mechanism :error_count()/:uuid() already
    # use, no finder-side code needed.
    #
    NAME = "named_paths_fingerprint"
    SUMMARY = (
        "The fingerprint of the named-paths group version whose content "
        "drove the resolved run. An optional string argument GATES a "
        "pooled candidate list by this field."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KIND = "fingerprint"
    KEY = {
        Reference3.RESULTS: "named_paths_fingerprint",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
