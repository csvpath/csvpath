from ...reference_3 import Reference3
from ..function_3 import Function3


class Username3(Function3):
    #
    # widened 2026-08-26 to also cover FILES/CSVPATHS -- Table 2 (Named-
    # File Arrivals Manifest, global) and Table 4 (Named-Paths Loads
    # Manifest, global) both have a "username" field, but neither Table
    # 1 (Named-File Manifest) nor Table 3 (Named-Paths Manifest) does --
    # confirmed against file_registrar.py/paths_registrar.py, this is a
    # genuinely ledger-only field for those two datatypes, unlike RESULTS
    # (where the run's own manifest already has it directly). KEY has no
    # FILES/CSVPATHS entry at all (nothing to find in the entity's own
    # manifest); LEDGER_KEY is the only source for those two, same shape
    # as :file_manifest()/:group_manifest().
    #
    NAME = "username"
    SUMMARY = (
        "The username of the process that performed the resolved "
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
        Reference3.RESULTS: "username",
    }
    LEDGER_KEY = {
        Reference3.FILES: "username",
        Reference3.CSVPATHS: "username",
    }
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }
