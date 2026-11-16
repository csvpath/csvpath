from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.does_not_have_value_3 import DoesNotHaveValue3
from ..filters.has_value_3 import HasValue3


class WebhooksOnCompleteValid3(Function3):
    #
    # see webhooks_on_complete_all_3.py for the shared four-fixed-field
    # design this follows (no argument -- not keyed by any name).
    #
    NAME = "webhooks_on_complete_valid"
    SUMMARY = (
        "The completion webhook (url/payload/headers) configured to "
        "fire only when the csvpath statement is valid, for the "
        "resolved named-paths group -- read from definition.json's "
        "webhooks.on_complete_valid. None if not configured."
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
        Reference3.CSVPATHS: "webhooks.on_complete_valid",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
