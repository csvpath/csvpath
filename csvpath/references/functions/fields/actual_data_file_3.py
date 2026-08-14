from ...reference_3 import Reference3
from ..function_3 import Function3


class ActualDataFile3(Function3):
    #
    # kept as a pair with origin_data_file_3.py -- they only mean
    # anything in contrast to each other, per manifest_field_functions_
    # proposal.md's Part B.
    #
    NAME = "actual_data_file"
    SUMMARY = (
        "The real input file path this instance actually read -- may "
        "not match the named-file path (e.g. source-mode-preceding or "
        "by_line runs read a different instance's data.csv instead)."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULT: "actual_data_file",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}
