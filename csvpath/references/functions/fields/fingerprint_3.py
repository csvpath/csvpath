from ...reference_3 import Reference3
from ..function_3 import Function3


class Fingerprint3(Function3):
    #
    # see uuid_3.py for the shared field-accessor design this follows.
    # deliberately not unified with the Results Run Manifest's
    # named_file_fingerprint or the Result Instance Manifest's
    # file_fingerprints -- those describe the fingerprint of other
    # content this result consumed/produced, not of the entity itself,
    # per manifest_field_functions_proposal.md's Part A note on this
    # function.
    #
    NAME = "fingerprint"
    SUMMARY = (
        "The content-integrity hash of the resolved named-file/named-"
        "paths version's own defining content (the file's bytes, or "
        "group.csvpaths' text) -- SHA256 in most cases; S3-backed "
        "content uses MD5 instead, per the same fingerprint mechanism "
        "used throughout the framework."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "fingerprint",
        Reference3.CSVPATHS: "fingerprint",
    }
