from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.does_not_have_value_3 import DoesNotHaveValue3
from ..filters.has_value_3 import HasValue3


class NamedFilePath3(Function3):
    #
    # Results Run Manifest (table 5)'s own "named_file_path" -- the
    # path to the named-file version used as this run's data input.
    # Deliberately distinct from FilePath3/:file_path() (the FILES
    # datatype's own version path) -- this is RESULTS' own record of
    # which file it consumed, not a FILES-side field.
    #
    NAME = "named_file_path"
    SUMMARY = "The path to the named-file version used as input to the resolved run."
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
        Reference3.RESULTS: "named_file_path",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
