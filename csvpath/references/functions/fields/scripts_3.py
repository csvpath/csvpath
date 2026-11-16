from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.does_not_have_value_3 import DoesNotHaveValue3
from ..filters.has_value_3 import HasValue3


class Scripts3(Function3):
    #
    # see on_arrival_3.py for the definition.json-backed field-accessor
    # design this follows. CSVPATHS side of the same on_complete_all/
    # on_complete_valid/on_complete_invalid/on_complete_error convention
    # webhooks_3.py and transfers_3.py also use.
    #
    NAME = "scripts"
    SUMMARY = (
        "The completion scripts configured for the resolved named-paths "
        "group -- on_complete_all/valid/invalid/error, each a script "
        "filename -- read from definition.json. Empty if none are "
        "configured."
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
        Reference3.CSVPATHS: "scripts",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
