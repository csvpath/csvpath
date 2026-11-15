from ...reference_3 import Reference3
from ..function_3 import Function3


class OriginDataFile3(Function3):
    #
    # kept as a pair with actual_data_file_3.py -- they only mean
    # anything in contrast to each other, per manifest_field_functions_
    # proposal.md's Part B. Deliberately NOT the same concept as
    # origin_3.py's FILES/CSVPATHS "origin" (where registered content
    # originally came from) -- this is about which physical file this
    # instance would read if every instance used the named-file
    # directly.
    #
    NAME = "origin_data_file"
    SUMMARY = (
        "The input file path this instance would read if all instances "
        "used the named-file directly, regardless of what it actually "
        "read -- see :actual_data_file() for that."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULT: "origin_data_file",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}
