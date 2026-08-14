from ...reference_3 import Reference3
from ..function_3 import Function3


class Having3(Function3):
    #
    # CSVPATHS-only version filter -- added 2026-08-13. Filters a named-
    # paths group's version manifest down to versions whose own
    # "named_paths_identities" list (confirmed against PathsRegistrar's
    # real manifest schema -- one entry per loaded/reloaded version,
    # already read by CsvpathsReferenceFinder3 for name_three identity
    # lookups) contains the given identity -- "the last version of this
    # group that actually HAS a statement named this" (a group's
    # statement set can change release to release; not every version
    # necessarily has every identity). Named after SQL's HAVING (filters
    # groups by a condition on their own contents, as opposed to WHERE,
    # which filters rows) -- David's own framing.
    #
    # ROLE is CONTEXT_SETTER, not POINTER -- it narrows the candidate
    # version list without resolving to exactly one; a real pointer
    # (":last()" etc.) riding alongside it reduces the FILTERED list,
    # the same "narrow, then optionally reduce" pattern ':all()'/
    # ':from()'/':to()' already use elsewhere in this codebase.
    #
    NAME = "having"
    SUMMARY = (
        "Filters this named-paths group's versions down to those whose "
        "own statement list contains a statement with this identity."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.CSVPATHS,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = True
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
