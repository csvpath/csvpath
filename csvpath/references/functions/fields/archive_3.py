from ...reference_3 import Reference3
from ..function_3 import Function3


class Archive3(Function3):
    #
    # Named-Paths Manifest (table 3)'s "archive_name" (the configured
    # [results] archive value at load time) and the Result Instance
    # Manifest (table 6)'s own "archive_name" (the archive dir name at
    # the time this result was generated) -- same literal key, same
    # concept (a snapshot of the archive dir name at some past moment),
    # different entities. RESULTS run scope (table 5) has no equivalent
    # field of its own -- confirmed against results_registrar.py, not
    # assumed -- but Table 7 (the Archive Run Manifest, RESULTS' own
    # global ledger) does carry an "archive_name" per statement
    # execution, so run scope falls back to that via LEDGER_KEY (added
    # 2026-08-26, see ResultsReferenceFinder3._find_archive_ledger_
    # entry()). Kept as one name across name/path too (David, 2026-08-26):
    # :archive() always means the NAME, matching CSVPATHS/RESULT's
    # existing meaning -- a genuinely different concept, the full
    # directory path, is :archive_path() instead (see that module),
    # mirroring the :file()/:file_path() split made earlier this session.
    #
    NAME = "archive"
    SUMMARY = (
        "The archive directory name in effect at the moment the "
        "resolved entity was created -- the named-paths group's own "
        "load-time snapshot, a result instance's own, or a result run's "
        "own (via the archive ledger's fallback entry)."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.CSVPATHS: "archive_name",
        # no Reference3.RESULTS entry here on purpose -- confirmed
        # against results_registrar.py, the run's own manifest (table 5)
        # never has this field, only Table 7's ledger entry does (see
        # LEDGER_KEY below).
        Reference3.RESULT: "archive_name",
    }
    LEDGER_KEY = {
        Reference3.RESULTS: "archive_name",
    }
    POSITIONS = {
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }
