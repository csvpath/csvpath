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
    # ARG_TYPES widened 2026-10-18 (was: `()`, bare-only) --
    # normative_reference_examples.txt's own worked example ("select
    # all runs that used a specific version of a named-file": "$*.
    # results.:flatten():named_file_fingerprint(\"4fd50acf...\")") needs
    # a string argument to GATE a pooled RESULTS candidate list by this
    # field -- part of compendium 6.7's "fingerprint" functional group
    # (:fingerprint()/:named_file_fingerprint()), the same retrieve/
    # select duality rule already built for :fingerprint() itself. Same
    # generic field_call/_matches_field_predicate mechanism :error_
    # count()/:uuid() already use, no finder-side code needed.
    #
    NAME = "named_file_fingerprint"
    SUMMARY = (
        "The fingerprint of the named-file version used as input to "
        "the resolved run. An optional string argument GATES a pooled "
        "candidate list by this field."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KIND = "fingerprint"
    KEY = {
        Reference3.RESULTS: "named_file_fingerprint",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
