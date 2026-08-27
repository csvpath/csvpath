from ...reference_3 import Reference3
from ..function_3 import Function3


class Hostname3(Function3):
    #
    # widened 2026-08-26 -- see username_3.py for the shared reasoning
    # (Tables 2/4's global ledgers have "hostname", Tables 1/3's own
    # per-entity manifests do not; RESULTS already has it directly).
    #
    NAME = "hostname"
    SUMMARY = (
        "The hostname of the machine that performed the resolved "
        "action -- registered/loaded a named-file/named-paths version "
        "(via the arrivals/loads ledger only), or executed a results "
        "run (directly on the run's own manifest)."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "hostname",
    }
    LEDGER_KEY = {
        Reference3.FILES: "hostname",
        Reference3.CSVPATHS: "hostname",
    }
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }
