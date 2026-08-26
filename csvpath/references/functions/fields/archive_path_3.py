from ...reference_3 import Reference3
from ..function_3 import Function3


class ArchivePath3(Function3):
    #
    # Table 7 (the Archive Run Manifest, RESULTS' own global ledger)
    # only -- the full path to the archive dir at the time a run
    # occurred. No per-entity manifest (run or instance) carries this
    # field at all, confirmed against results_registrar.py/
    # result_registrar.py -- KEY is empty on purpose, LEDGER_KEY is the
    # only source. Kept as a separate name from :archive() (which means
    # the archive dir's NAME, not its path), mirroring the :file()/
    # :file_path() split made earlier this session -- David, 2026-08-26.
    #
    NAME = "archive_path"
    SUMMARY = (
        "The full path to the archive dir at the time the resolved "
        "run occurred, read from the archive ledger's own entry for "
        "that run (Table 7)."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {}
    LEDGER_KEY = {
        Reference3.RESULTS: "archive_path",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
