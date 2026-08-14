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
    # ARG_TYPES accepts an optional str -- added 2026-08-13, for FILES
    # only, to support the bare-lookup shape
    # ("$alpha.files.:fingerprint('hash...')", no :name(...) needed):
    # search the WHOLE named-file's manifest for the entry whose own
    # fingerprint matches, since content-hash identity does not care
    # which file/path slot a version happens to be registered under
    # (unlike :name(), which matches file_home, a path identity). See
    # FilesReferenceFinder3._is_bare_fingerprint_reference/query() for
    # where this is actually recognized and handled -- this class's own
    # ROLE stays VALUE (unchanged) specifically so it keeps NOT counting
    # as a second pointer when it rides alongside a real one in its
    # ordinary field-accessor position (e.g.
    # ":name('orders.csv').:first():fingerprint()"); the bare-lookup
    # shape is recognized structurally (bare, sole content of name_one,
    # WITH an arg), the same way ':all()'/':flatten()'/':groups()'/
    # ':home()' are already recognized, not via ROLE.
    #
    NAME = "fingerprint"
    SUMMARY = (
        "The content-integrity hash of the resolved named-file/named-"
        "paths version's own defining content (the file's bytes, or "
        "group.csvpaths' text) -- SHA256 in most cases; S3-backed "
        "content uses MD5 instead, per the same fingerprint mechanism "
        "used throughout the framework. For FILES only, also usable "
        "bare with a known hash to look up the specific version it "
        "identifies, across every path under a named-file."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "fingerprint",
        Reference3.CSVPATHS: "fingerprint",
    }
    #
    # CSVPATHS has no bare-lookup shape (that's FILES-only, see above) --
    # always the ordinary field-accessor position.
    #
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
