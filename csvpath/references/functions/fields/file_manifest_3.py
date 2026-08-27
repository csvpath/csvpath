from ...reference_3 import Reference3
from ..function_3 import Function3


class FileManifest3(Function3):
    #
    # Named-File Arrivals Manifest (table 2, the global ledger)'s own
    # "file_manifest" -- a pointer, from within the ledger entry, back to
    # the named-file's own manifest.json. The named-file's own manifest
    # (table 1) has no equivalent self-reference at all -- confirmed a
    # real core-Framework gap, see issue #261 -- so this is the first
    # real consumer of Function3.LEDGER_KEY: KEY is empty (nothing to
    # find in the entity's own manifest), LEDGER_KEY is the only place
    # this value can come from. Per David's own framing (2026-08-25): a
    # reference resolves one conceptual entity, not "one manifest entry
    # here, another there" -- the caller should not need to know this
    # field only lives in the ledger.
    #
    NAME = "file_manifest"
    SUMMARY = "The path to the resolved named-file's own manifest.json."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {}
    LEDGER_KEY = {
        Reference3.FILES: "file_manifest",
    }
    POSITIONS = {Reference3.FILES: (Reference3.NAME_THREE,)}
