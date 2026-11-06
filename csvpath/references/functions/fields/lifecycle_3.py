from ...reference_3 import Reference3
from ..function_3 import Function3


class Lifecycle3(Function3):
    #
    # the root ledger lifecycle of an entry, in every datatype: "active"
    # (Registrar.ACTIVE) when written, "deleted" (Registrar.DELETED) once
    # its named-file, named-paths group or named-results is deleted.
    # ledger-only: no per-name manifest or run manifest holds it, so it
    # is a LEDGER_KEY, never a KEY (the same as FILES' :status()). with
    # a string argument it is a GATE, :lifecycle("active"); without one,
    # the field (David, 2026-10-29). an entry written before
    # harmonization PR 6 has no lifecycle and matches neither: absence
    # implies nothing.
    #
    NAME = "lifecycle"
    SUMMARY = (
        "The root ledger lifecycle of an entry -- 'active' or 'deleted'. "
        "With a string argument, a filter, e.g. ':lifecycle(\"active\")'."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {}
    LEDGER_KEY = {
        Reference3.FILES: "lifecycle",
        Reference3.CSVPATHS: "lifecycle",
        Reference3.RESULTS: "lifecycle",
    }
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_ONE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }
