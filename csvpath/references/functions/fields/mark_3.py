from ...reference_3 import Reference3
from ..function_3 import Function3


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
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "mark",
    }
