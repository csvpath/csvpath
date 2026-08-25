from ...reference_3 import Reference3
from ..function_3 import Function3


class GroupManifest3(Function3):
    #
    # Named-Paths Loads Manifest (table 4, the global ledger)'s own
    # "paths_manifest" -- a pointer, from within the ledger entry, back
    # to the named-paths group's own manifest.json. See file_manifest_3.py
    # for the shared LEDGER_KEY-only design this follows (KEY is empty --
    # the named-paths group's own manifest has no equivalent self-
    # reference field either, confirmed against paths_registrar.py).
    #
    NAME = "group_manifest"
    SUMMARY = "The path to the resolved named-paths group's own manifest.json."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {}
    LEDGER_KEY = {
        Reference3.CSVPATHS: "paths_manifest",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
