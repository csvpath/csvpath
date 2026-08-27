from ...reference_3 import Reference3
from ..function_3 import Function3


class FileFingerprints3(Function3):
    #
    # dict-shaped (per generated file), not a scalar -- structurally
    # different from fingerprint_3.py, per manifest_field_functions_
    # proposal.md's Part B. Still KIND = "fingerprint" (2026-08-26) --
    # UNION only cares whether the two sides' accessors are conceptually
    # comparable, never their resolved value's shape, so the dict-vs-
    # scalar difference doesn't disqualify it here. SUBTRACT/INTERSECT
    # still reject a dict-valued join key regardless of KIND (see
    # ReferenceExpression3._hashable) -- unaffected by this.
    #
    NAME = "file_fingerprints"
    SUMMARY = (
        "The content-integrity hashes of the resolved instance's own "
        "generated files (data.csv, meta.json, etc.), keyed by "
        "filename."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KIND = "fingerprint"
    KEY = {
        Reference3.RESULT: "file_fingerprints",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}
