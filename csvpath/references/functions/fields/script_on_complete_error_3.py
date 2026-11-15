from ...reference_3 import Reference3
from ..function_3 import Function3


class ScriptOnCompleteError3(Function3):
    #
    # see script_on_complete_all_3.py for the shared four-fixed-field
    # design this follows (no argument -- not keyed by any name).
    #
    NAME = "script_on_complete_error"
    SUMMARY = (
        "The completion script filename configured to run only when "
        "the csvpath statement has errors, for the resolved named-paths "
        "group -- read from definition.json's scripts.on_complete_error. "
        "None if not configured."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "definition"
    KEY = {
        Reference3.CSVPATHS: "scripts.on_complete_error",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
