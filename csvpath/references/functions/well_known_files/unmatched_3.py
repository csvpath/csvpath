from ...reference_3 import Reference3
from ..function_3 import Function3


class Unmatched3(Function3):
    #
    # resolves to the raw bytes of unmatched.csv -- the unmatched-line
    # output a csvpath statement's own run instance wrote
    # (ResultSerializer._save -- only written if there is at least one
    # unmatched line; genuinely optional, resolves to None rather than
    # raising when absent). See Errors3 for the shared name_three shape
    # this rides alongside.
    #
    NAME = "unmatched"
    SUMMARY = (
        "The raw bytes of a run instance's unmatched.csv -- the "
        "unmatched-line output that csvpath statement's execution "
        "wrote. None if nothing was unmatched (the file was never "
        "written)."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
