from ...reference_3 import Reference3
from ..function_3 import Function3


class RunMethod3(Function3):
    #
    # Named-File Definition (table 8)'s own "on_arrival.run_method" --
    # see named_paths_group_3.py/on_arrival_3.py for the shared
    # definition.json-backed design this follows. Deliberately a
    # different NAME than Method3/:method() (the Results Run Manifest's
    # own, already-happened run method) -- this is the *configured*
    # method to invoke on arrival, not a record of one that already ran.
    #
    NAME = "run_method"
    SUMMARY = (
        "The method to invoke (e.g. 'collect_paths') when the resolved "
        "named-file's on_arrival activation triggers, from "
        "definition.json's on_arrival config."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "definition"
    KEY = {
        Reference3.FILES: "on_arrival.run_method",
    }
    POSITIONS = {Reference3.FILES: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
