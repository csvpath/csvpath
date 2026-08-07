from ...reference_3 import Reference3
from ..function_3 import Function3


class Data3(Function3):
    #
    # resolves to the raw bytes of data.csv -- the matched-line output a
    # csvpath statement's own run instance wrote
    # (ResultSerializer._save -- only written if there is at least one
    # matched line; genuinely optional, same as definition.json,
    # resolves to None rather than raising when absent). See Errors3 for
    # the shared name_three shape this rides alongside.
    #
    NAME = "data"
    SUMMARY = (
        "The raw bytes of a run instance's data.csv -- the matched-line "
        "output that csvpath statement's execution wrote. None if no "
        "lines matched (the file was never written)."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
