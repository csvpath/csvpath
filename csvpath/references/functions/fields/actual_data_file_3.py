from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.does_not_have_value_3 import DoesNotHaveValue3
from ..filters.has_value_3 import HasValue3


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
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    # and :has_value()/:does_not_have_value(): "Every field matches exactly
    # one of the two" (NRE); other predicates on a string are not ruled
    ARG_TYPES = (str, HasValue3, DoesNotHaveValue3)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULT: "actual_data_file",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}
