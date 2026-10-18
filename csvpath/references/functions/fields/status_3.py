from ...reference_3 import Reference3
from ..function_3 import Function3


class Status3(Function3):
    #
    # RESULTS: run scope only -- a lifecycle marker ("started"/
    # "complete"), bare only (no GATE use -- ARG_TYPES stays empty for
    # this datatype's own purposes, see below).
    #
    # FILES widened 2026-10-18 -- "not to be confused with the FILES
    # ledger's own status (a failure message, unexposed today)" turned
    # out to be exactly what normative_reference_examples.txt's own
    # worked example needed exposed: "$*.files.:status(\"Registration
    # failed\"):named_file_name(\"orders\")" ("select named-files
    # registrations for orders that failed"). Traced the real write
    # path (not guessed) before building: `file_manager.py`'s own
    # `mdata.status = "Registration failed"`, written via
    # `FilesListener.metadata_update()` -- confirmed this lands ONLY in
    # the GLOBAL arrivals ledger (`files_root_manifest`), never any
    # per-name manifest (a failed registration often has no real name/
    # path to file itself under). The field name is confirmed as
    # literally "status", same literal key RESULTS already uses, per
    # manifest_field_functions_proposal.md's Part B note -- different
    # concept (a failure message, not a lifecycle marker), same name,
    # same KEY string, by coincidence not design. KEY has NO FILES
    # entry -- per `username_3.py`'s own established precedent for a
    # genuinely ledger-only field, this goes in LEDGER_KEY instead
    # (confirmed: status is NEVER written to any per-name manifest).
    # This also matters structurally, not just semantically:
    # FilesReferenceFinder3._extract_gate_field_call() (the ':type()'-
    # style single-GATE mechanism, which filters PER-NAME manifest
    # candidates) explicitly excludes any candidate whose own
    # `KEY.get(Reference3.FILES)` is empty -- confirmed live this
    # guard is needed, not just theoretical: without it, a combination
    # no worked example asks for (e.g. ":flatten():status(\"x\")")
    # would silently match nothing instead of being correctly routed
    # to the ledger-reading path below, since no per-name manifest
    # entry has a "status" key at all.
    #
    # POSITIONS for FILES is NAME_ONE-only (no NAME_THREE) -- status is
    # NEVER written to a per-name manifest, so reading it off an
    # already-resolved specific version (the ordinary field-read
    # position every other FILES field accessor eventually gets) would
    # never have real data; this function only ever means anything as
    # the GATE/chain-detection trigger in FilesReferenceFinder3's own
    # new `_bare_status_gate_chain()` (see its own docstring), which
    # reads the global ledger directly rather than going through the
    # ordinary per-name-manifest candidate pipeline at all.
    #
    NAME = "status"
    SUMMARY = (
        "RESULTS: the lifecycle status of the resolved run -- "
        "'started' or 'complete', bare only. FILES: a failure message "
        "('Registration failed') recorded in the global arrivals "
        "ledger -- always takes a string argument there, GATE-ing a "
        "bare chain read directly from that ledger (e.g. ':status("
        "\"Registration failed\"):named_file_name(\"orders\")')."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS, Reference3.FILES)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "status",
    }
    LEDGER_KEY = {
        Reference3.FILES: "status",
    }
    POSITIONS = {
        Reference3.RESULTS: (Reference3.NAME_ONE,),
        Reference3.FILES: (Reference3.NAME_ONE,),
    }
