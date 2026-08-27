from ...reference_3 import Reference3
from ..function_3 import Function3


class Printouts3(Function3):
    #
    # resolves to the raw bytes of printouts.txt -- the standard
    # printouts under print-mode's combined-output default, a csvpath
    # statement's own run instance wrote (same directory level as
    # data.csv/errors.json -- see run_home_maker.py's own worked
    # example path). Genuinely optional, same as data.csv/
    # unmatched.csv -- resolves to None rather than raising when
    # absent (nothing was ever printed). See Errors3 for the shared
    # name_three shape this rides alongside.
    #
    NAME = "printouts"
    SUMMARY = (
        "The raw bytes of a run instance's printouts.txt -- the "
        "standard printouts under print-mode's combined-output "
        "default. None if nothing was printed (the file was never "
        "written)."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}
