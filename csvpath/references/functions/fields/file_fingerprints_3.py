from ...reference_3 import Reference3
from ..function_3 import Function3


class FileFingerprints3(Function3):
    #
    # dict-shaped (per generated file), not a scalar -- structurally
    # different from fingerprint_3.py, per manifest_field_functions_
    # proposal.md's Part B.
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
    KEY = {
        Reference3.RESULT: "file_fingerprints",
    }
