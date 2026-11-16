from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.does_not_have_value_3 import DoesNotHaveValue3
from ..filters.has_value_3 import HasValue3


class WebhooksOnCompleteAll3(Function3):
    #
    # webhooks_3.py's own "webhooks" object has exactly four fixed
    # sub-fields (on_complete_all/valid/invalid/error), confirmed
    # against the real Webhooks dataclass (paths_descriptor.py) -- not
    # keyed by any arbitrary name, so this takes no argument.
    #
    NAME = "webhooks_on_complete_all"
    SUMMARY = (
        "The completion webhook (url/payload/headers) configured to "
        "fire regardless of outcome, for the resolved named-paths "
        "group -- read from definition.json's webhooks.on_complete_all. "
        "None if not configured."
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
        Reference3.CSVPATHS: "webhooks.on_complete_all",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
