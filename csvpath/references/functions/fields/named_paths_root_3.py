from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedPathsRoot3(Function3):
    #
    # Table 7 (the Archive Run Manifest) only -- the [inputs] csvpaths
    # value from config.ini at the time a run occurred. No per-entity
    # manifest carries this, confirmed against results_registrar.py/
    # result_registrar.py -- KEY is empty, LEDGER_KEY is the only
    # source.
    #
    NAME = "named_paths_root"
    SUMMARY = (
        "The location of the named-paths ([inputs] csvpaths in "
        "config.ini) at the time the resolved run occurred, read from "
        "the archive ledger's own entry for that run (Table 7)."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {}
    LEDGER_KEY = {
        Reference3.RESULTS: "named_paths_root",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
