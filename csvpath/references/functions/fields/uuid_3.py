from ...reference_3 import Reference3
from ..function_3 import Function3


class Uuid3(Function3):
    #
    # first of the shared, context-dispatching field-accessor functions
    # (see references_notes/notes/manifest_field_functions_proposal.md,
    # Part A) -- reads the "uuid" key straight off the manifest entry a
    # pointer (or the absence of one) already resolved, exactly the way
    # :manifest() itself rides alongside a pointer, except this pulls one
    # field out instead of handing back the whole entry.
    #
    # RESULTS is instance-only (Reference3.RESULT, not Reference3.
    # RESULTS): a run's own bare "uuid" field (table 5) is the excluded,
    # vestigial one (see project_manifest_field_review_issues) -- an
    # instance's own "uuid" (table 6) is the real, meaningful one. No
    # Reference3.RESULTS entry means :uuid() used at run scope correctly
    # resolves to None (_extract_field_value's tolerant missing-key
    # behavior) rather than accidentally surfacing the deprecated field.
    # See run_uuid_3.py for "which run this belongs to" instead.
    #
    NAME = "uuid"
    SUMMARY = (
        "The uuid of the resolved named-file/named-paths version, or "
        "results instance -- the registration/load/instance event's own "
        "identifier, read straight off its manifest entry. Not "
        "available at RESULTS run scope -- that field is deprecated; "
        "see :run_uuid()."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "uuid",
        Reference3.CSVPATHS: "uuid",
        Reference3.RESULT: "uuid",
    }
