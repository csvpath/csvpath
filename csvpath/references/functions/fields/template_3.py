from ...reference_3 import Reference3
from ..function_3 import Function3


class Template3(Function3):
    #
    # the first field accessor needing Function3.BARE_SOURCE -- settled
    # with David 2026-08-26. "template" genuinely means two different
    # things depending on whether a real pointer selected a specific
    # version:
    #   - riding alongside a real pointer (e.g. FILES'
    #     ":name(\"x\").:first():template()", CSVPATHS'
    #     "$acme.csvpaths.:first():template()") -- the template actually
    #     used for THAT registration/load event, a historical snapshot
    #     stored on that version's own manifest entry (Table 1/Table 3).
    #     Ordinary SOURCE == "manifest" behavior, unchanged from every
    #     other per-version field accessor.
    #   - bare, no pointer at all -- the entity's CURRENT default
    #     template, read from definition.json instead (Table 8/Table 9).
    #     BARE_SOURCE == "definition". Table 9's own docstring is
    #     explicit about this being the real distinction: "This is the
    #     actual source of truth read by PathsManager.
    #     get_template_for_paths() at load time -- the Named-Paths
    #     Manifest's own template field (table 3) is a snapshot of
    #     whatever this held at that particular load, not an
    #     independently-set value. The two can only diverge if this is
    #     edited after a version was already loaded."
    #
    # RESULTS is simpler -- no bare/definition duality at all, since a
    # run is not a versioned, editable config artifact the way a named-
    # file/named-paths registration is. Confirmed live against current
    # code (results_registrar.py line 121, run_registrar.py line 51):
    # both the per-run manifest (Table 5) and the archive-root ledger
    # (Table 7) already write "template" directly and unconditionally --
    # this was believed to be a blocking gap as recently as 2026-08-25,
    # corrected once re-checked. Table 5's own doc row is missing this
    # field entirely (a real doc gap, flagged separately, not fixed
    # here) -- built from the confirmed code, not the doc. Ordinary
    # SOURCE == "manifest" plus LEDGER_KEY fallback to Table 7, same
    # shape as every other RESULTS run-scope field.
    #
    NAME = "template"
    SUMMARY = (
        "The template in effect for the resolved entity -- the "
        "specific version's own historical snapshot when a real "
        "pointer selected one, or the entity's current default from "
        "definition.json when used bare. For RESULTS, simply the "
        "run's own template, no bare/current distinction."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    BARE_SOURCE = "definition"
    KEY = {
        Reference3.FILES: "template",
        Reference3.CSVPATHS: "template",
        Reference3.RESULTS: "template",
    }
    LEDGER_KEY = {
        Reference3.RESULTS: "template",
    }
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
        Reference3.RESULTS: (Reference3.NAME_ONE,),
    }
