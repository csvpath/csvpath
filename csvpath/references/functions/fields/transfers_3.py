from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.does_not_have_value_3 import DoesNotHaveValue3
from ..filters.has_value_3 import HasValue3


class Transfers3(Function3):
    #
    # see on_arrival_3.py for the definition.json-backed field-accessor
    # design this follows. CSVPATHS-only for now -- the Result Instance
    # Manifest also has a per-instance "transfers" field (issue #224:
    # that one only records the old transfer-mode metadata transfers,
    # never these descriptor-based ones), which needs the RESULTS
    # instance-scope dispatch mechanism this batch is deliberately not
    # building yet. See manifest_field_functions_proposal.md's Part B.
    #
    NAME = "transfers"
    SUMMARY = (
        "The descriptor-based transfers configured for the resolved "
        "named-paths group, keyed by csvpath statement identity, each "
        "with on_complete_all/valid/invalid/error lists of file/"
        "transfer_to pairs -- read from definition.json's "
        "transfers.path_transfers. Note: on_complete_invalid and "
        "on_complete_error are accepted by the schema but not currently "
        "triggered at runtime -- see issue #226."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    # a collection: only the value predicates filter it -- an equality
    # test on a dict means nothing (RC triage B5, David 2026-11-16;
    # compendium 6.40). The ':definition()' chain applies it per group.
    ARG_TYPES = (HasValue3, DoesNotHaveValue3)
    ARG_REQUIRED = False
    SOURCE = "definition"
    KEY = {
        Reference3.CSVPATHS: "transfers.path_transfers",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
