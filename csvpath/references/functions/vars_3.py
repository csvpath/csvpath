from ..reference_3 import Reference3
from .function_3 import Function3


class Vars3(Function3):
    #
    # resolves to the parsed JSON contents of vars.json, the variables a
    # csvpath statement's own run instance captured
    # (ResultSerializer._save_vars -- written via jsonpickle with
    # unpicklable=False, so plain JSON, parseable the same as any other
    # well-known JSON file here). See Errors3 for the shared name_three
    # shape this rides alongside.
    #
    NAME = "vars"
    SUMMARY = (
        "The parsed contents of a run instance's vars.json -- the "
        "variables that csvpath statement's execution captured."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
