from ...reference_3 import Reference3
from ..function_3 import Function3


class ScriptOnCompleteAll3(Function3):
    #
    # scripts_3.py's own "scripts" object has exactly four fixed
    # sub-fields (on_complete_all/valid/invalid/error), confirmed
    # against the real Scripts dataclass (paths_descriptor.py) -- not
    # keyed by any arbitrary name, unlike sources/destinations/
    # transfers, so this takes no argument (the required-manifest-
    # functions doc's own "(str)" on two of the four scripts accessors
    # was a leftover copy-paste artifact, confirmed and dropped here).
    #
    NAME = "script_on_complete_all"
    SUMMARY = (
        "The completion script filename configured to run regardless "
        "of outcome, for the resolved named-paths group -- read from "
        "definition.json's scripts.on_complete_all. None if not "
        "configured."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "definition"
    KEY = {
        Reference3.CSVPATHS: "scripts.on_complete_all",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
