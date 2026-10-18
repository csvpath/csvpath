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
    # ARG_TYPES widened 2026-10-18 (was: `()`, bare-only), plus
    # SELECTOR_WHEN_ARGUED -- the compendium's own stated rule for the
    # "uuid" functional group (normative_reference_examples.txt
    # ~232-234): "a function that represents a unique identifier field
    # may retrieve the value when used without an argument, [or]
    # select an entity when its value matches the function's
    # argument." Two normative worked examples needed this directly:
    #   $acme.files.:uuid("ab37-fef3...")
    #   $acme.csvpaths.:uuid("45ad7aa7-fe08-4f18-8b1b-e2d11675bf36")
    # Same mechanism :fingerprint() already has (see its own
    # docstring) -- FILES picks this up for free via the existing
    # registry-driven ReferenceFinder3._is_bare_selector_reference()/
    # FilesReferenceFinder3.query() dispatch; CsvpathsReferenceFinder3
    # needed a new dispatch branch of its own (CSVPATHS never had a
    # bare-lookup shape for ANY function before -- Fingerprint3's own
    # docstring is explicit that it is FILES-only). As a side effect,
    # also correctly enables RESULTS' own GATE use (e.g. ":manifest():
    # uuid(\"a381...\"):run_home()", confirmed live) via the fully
    # generic field_call/_matches_field_predicate mechanism :error_
    # count()/:named_file_name() already use -- no RESULTS-side code
    # needed, since that mechanism keys on "does this chain member
    # carry an arg," never on which function it is.
    #
    NAME = "uuid"
    SUMMARY = (
        "The uuid of the resolved named-file/named-paths version, or "
        "results run/instance -- the registration/load/run/instance "
        "event's own identifier. At RESULTS run scope this is the same "
        "value as :run_uuid() (the run's own bare 'uuid' field is "
        "deprecated and not read here). An optional string argument "
        "either SELECTS the entity whose own uuid matches (FILES/"
        "CSVPATHS, bare, no pointer -- e.g. ':uuid(\"ab37-fef3...\")') "
        "or GATES a pooled '*'/':flatten()'/':manifest()' RESULTS "
        "candidate list by this field (same GATE mechanism :error_"
        "count() uses)."
    )
    SELECTOR_WHEN_ARGUED = True
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KIND = "uuid"
    KEY = {
        Reference3.FILES: "uuid",
        Reference3.CSVPATHS: "uuid",
        Reference3.RESULTS: "run_uuid",
        Reference3.RESULT: "uuid",
    }
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        # RESULTS: KEY has both RESULTS ("run_uuid", per the class's own
        # docstring on why run scope reads that instead of a deprecated
        # bare "uuid") and RESULT ("uuid", instance scope) entries.
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }
