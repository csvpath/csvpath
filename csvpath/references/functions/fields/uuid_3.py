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
    # RESULTS run scope reads "run_uuid", not the run's own bare "uuid"
    # field (table 5) -- that field is deprecated/vestigial (see
    # project_manifest_field_review_issues) and its setter already
    # mirrors run_uuid's value (PR #231), so reading run_uuid here gives
    # the identical value without resurrecting any dependency on the
    # field slated for eventual removal. Settled 2026-08-11: "this
    # entity's own id" and "which run this belongs to" trivially
    # coincide AT run scope (the run has no further container above it
    # to diverge from) -- the caution that is genuinely needed at
    # instance scope (an instance's own id really is different from its
    # containing run's) does not apply at run scope, so :uuid() should
    # not withhold a value there the way it used to. See run_uuid_3.py
    # for the same value under its own, always-available name.
    #
    NAME = "uuid"
    SUMMARY = (
        "The uuid of the resolved named-file/named-paths version, or "
        "results run/instance -- the registration/load/run/instance "
        "event's own identifier. At RESULTS run scope this is the same "
        "value as :run_uuid() (the run's own bare 'uuid' field is "
        "deprecated and not read here)."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "uuid",
        Reference3.CSVPATHS: "uuid",
        Reference3.RESULTS: "run_uuid",
        Reference3.RESULT: "uuid",
    }
    POSITIONS = {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}
