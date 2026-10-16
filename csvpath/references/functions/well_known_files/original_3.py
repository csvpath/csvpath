from ...reference_3 import Reference3
from ..function_3 import Function3


class Original3(Function3):
    #
    # resolves to the raw bytes of original.<ext> -- a byte copy of the
    # registered data file the run started from (orders.csv/.xml/.json/
    # .xlsx/...), written by collect_original() (#341, #350 on the
    # bucket list). Same file in every source mode, including
    # source-mode: preceding. Genuinely optional (collect_original() is
    # opt-in) -- resolves to None rather than raising when absent, same
    # treatment as data.csv/unmatched.csv. See Errors3 for the shared
    # name_three shape this rides alongside.
    #
    # Unlike every other well-known RESULTS file, the file's own
    # extension varies by source type, so it cannot be looked up by a
    # fixed name the way data.csv/errors.json/etc are -- confirmed
    # against ResultRegistrar._original_file() (the same framework
    # convention this mirrors) before building: it is located by
    # listing the instance directory and matching the "original." prefix
    # (OriginalFileUtility.NAME), not a fixed "original.csv". See
    # ResultsReferenceFinder3._read_accessor()'s own "original" branch
    # for the matching lookup.
    #
    NAME = "original"
    SUMMARY = (
        "The raw bytes of a run instance's original.<ext> -- a byte "
        "copy of the registered data file the run started from. None "
        "if collect_original() was never used (it is opt-in)."
    )
    ROLE = Function3.VALUE
    # metadata_kind() override -- a whole-resource read, not a
    # single field, see Function3.RESOLVES_AS's own docstring for
    # why this class needs one (added 2026-08-28).
    RESOLVES_AS = Reference3.METADATA_FILE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}
