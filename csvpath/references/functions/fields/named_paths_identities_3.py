from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.does_not_have_value_3 import DoesNotHaveValue3
from ..filters.has_value_3 import HasValue3


class NamedPathsIdentities3(Function3):
    #
    # see uuid_3.py for the shared field-accessor design this follows.
    # single-context (CSVPATHS only), per
    # manifest_field_functions_proposal.md's Part B.
    #
    NAME = "named_paths_identities"
    SUMMARY = (
        "The list of csvpath statement identities (explicit :id/:name "
        "metadata, or the stringified load-time index for an unnamed "
        "statement) for the resolved named-paths group version."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.CSVPATHS,)
    # a collection: only the value predicates filter it -- an equality
    # test on a list or dict means nothing (RC triage B5, David
    # 2026-11-16; compendium 6.40)
    ARG_TYPES = (HasValue3, DoesNotHaveValue3)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.CSVPATHS: "named_paths_identities",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
