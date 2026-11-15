from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.does_not_have_value_3 import DoesNotHaveValue3
from ..filters.has_value_3 import HasValue3


class Mark3(Function3):
    #
    # see uuid_3.py for the shared field-accessor design this follows.
    # single-context (FILES only) -- no recurring "mark" concept
    # elsewhere in the catalog, per manifest_field_functions_proposal.md's
    # Part B.
    #
    NAME = "mark"
    SUMMARY = (
        "The Excel worksheet name of the resolved named-file version, "
        "when the registration targeted a specific worksheet rather "
        "than a whole workbook. None if the version has no mark."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    # and :has_value()/:does_not_have_value(): "Every field matches exactly
    # one of the two" (NRE); other predicates on a string are not ruled
    ARG_TYPES = (str, HasValue3, DoesNotHaveValue3)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "mark",
    }
    POSITIONS = {Reference3.FILES: (Reference3.NAME_THREE,)}
