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
    # Widened to RESULTS 2026-08-27 (deferred-work bucket-list entry,
    # "':having()' is not yet built for RESULTS at all") -- the same
    # underlying idea one level down: filters the candidate RUN pool
    # down to runs that contain an instance (a csvpath statement result)
    # with the given identity, using ResultsReferenceFinder3's own
    # _list_instance_identities() (a filesystem listing, unlike
    # CSVPATHS' own manifest-array membership check -- RESULTS has no
    # equivalent "named_paths_identities" field to read, each run's own
    # instance directories ARE the identity list). This is a real,
    # previously-unbuilt capability, distinct from just using a literal
    # identity in name_three -- a literal identity SELECTS one instance
    # (returns the instance itself, silently empty for a non-matching
    # run); ':having()' here rides in name_one, alongside a pointer like
    # ':last()', and FILTERS which runs even qualify before the pointer
    # picks one -- "the last run that had a header_checks statement,"
    # returning the RUN, not the instance (references_v3_expressions.md's
    # own Q&A distinguishes these two: INTERSECT-with-CSVPATHS for "give
    # me the runs," ':having()' directly on RESULTS for "give me the
    # instances" -- but the run-filtering shape here, confirmed with
    # David 2026-08-27, is a third, equally real shape neither of those
    # two examples covered explicitly).
    #
    # ROLE is CONTEXT_SETTER, not POINTER -- it narrows the candidate
    # version/run list without resolving to exactly one; a real pointer
    # (":last()" etc.) riding alongside it reduces the FILTERED list,
    # the same "narrow, then optionally reduce" pattern ':all()'/
    # ':from()'/':to()' already use elsewhere in this codebase.
    #
    NAME = "having"
    SUMMARY = (
        "Filters this named-paths group's versions, or (RESULTS) this "
        "group's runs, down to those whose own statement/instance list "
        "contains one with this identity."
    )
    ROLE = Function3.CONTEXT_SETTER
    DATATYPES = (Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = (str,)
    ARG_REQUIRED = True
    POSITIONS = {
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }
