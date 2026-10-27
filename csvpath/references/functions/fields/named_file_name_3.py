from ...reference_3 import Reference3
from ..function_3 import Function3


class NamedFileName3(Function3):
    #
    # at RESULTS/RESULT scope this reads a genuinely stored field --
    # which named-file a run/instance consumed, operational data that
    # cannot be derived any other way. At FILES scope it means something
    # different: the resolved entity's own name, which is already known
    # the moment a reference is parsed (reference.root_major) -- storing
    # it a second time in the Named-File Manifest would just be a
    # duplicate of something the finder already has in hand, so
    # FilesReferenceFinder3 computes it directly rather than reading it
    # from any manifest. Settled 2026-08-09, see
    # manifest_field_functions_proposal.md.
    #
    # ARG_TYPES widened 2026-10-18 (was: `()`, bare-only) --
    # normative_reference_examples.txt's own worked example needs a
    # string argument to GATE a pooled/grouped '*' candidate list by
    # this field: "$*.results.:groups():named_file_name(\"orders\"):
    # first()" ("select the first run for each template for runs
    # having the named-file name orders"). Reuses the exact generic
    # field_call/_matches_field_predicate GATE mechanism
    # :error_count() got the same day (ResultsReferenceFinder3's own
    # ":error_count(0)" exact-match case is structurally identical --
    # a bare leaf value compared with `==`) -- no finder-side change
    # needed. At FILES scope's own SINGLE-RESOLVED-NAME position (the
    # "computed" branch just above, always returning reference.
    # root_major) an argument still has no meaning and is still
    # ignored there -- unchanged.
    #
    # LEDGER_KEY added 2026-10-18, alongside ':status()'s own FILES
    # build -- a SECOND, genuinely different FILES position: chained
    # onto a bare ':status(...)' GATE reading the global arrivals
    # ledger directly (e.g. ":status(\"failed\"):
    # named_file_name(\"orders\")", normative_reference_examples.txt's
    # own worked example), this reads the real "named_file_name" field
    # the ledger already carries on every entry (confirmed live --
    # other code in this file already reads e["named_file_name"]
    # directly) -- NOT the "computed" derivation, which only applies
    # to the single-resolved-name position (SOURCE == "computed" is
    # checked, and wins, before KEY is ever consulted there -- see
    # FilesReferenceFinder3._extract_data()'s own dispatch -- so this
    # addition changes nothing about that existing, unchanged
    # behavior). Goes in LEDGER_KEY, not KEY -- per `username_3.py`'s
    # own established precedent for a genuinely ledger-only field
    # (confirmed: no per-name manifest entry has a "named_file_name"
    # key at all). This also matters structurally: Files
    # ReferenceFinder3._extract_gate_field_call() (the EARLIER,
    # ':type()'-style single-GATE mechanism, which filters PER-NAME
    # manifest candidates) explicitly excludes any candidate whose own
    # `KEY.get(Reference3.FILES)` is empty, so using LEDGER_KEY here
    # keeps this cleanly out of that mechanism's reach without also
    # needing a POSITIONS change (left at its original NAME_THREE-only
    # for FILES).
    #
    NAME = "named_file_name"
    SUMMARY = (
        "RESULTS/RESULT: the name of the named-file a run/instance "
        "consumed as its input, OPTIONALLY GATED by an exact-match "
        "string argument (e.g. ':named_file_name(\"orders\")') to "
        "filter a pooled/grouped '*' candidate list. FILES: the "
        "resolved named-file's own name (an argument there is "
        "ignored) -- OR, chained onto a bare ':status(...)' global-"
        "ledger GATE, this same field read directly off each ledger "
        "entry, GATED by its own argument there instead."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS, Reference3.FILES)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KIND = "name"
    KEY = {
        Reference3.RESULTS: "named_file_name",
        Reference3.RESULT: "named_file_name",
    }
    LEDGER_KEY = {
        Reference3.FILES: "named_file_name",
    }
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }
