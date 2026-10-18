from ...reference_3 import Reference3
from ..function_3 import Function3


class Type3(Function3):
    #
    # Named-File Manifest (table 1), per manifest_keys_reference_v2.md --
    # the file extension of the registered version (e.g. "csv", "xlsx").
    # Global-ledger scope (table 2's own "type") deferred alongside the
    # rest of the global-ledger batch.
    #
    # ARG_TYPES widened 2026-10-18 (was: `()`, bare-only) -- compendium
    # 3.9d's own claimed equivalence (":type(\"csv\")" == "*:type(
    # \"csv\")") plus its own worked examples (normative_reference_
    # examples.txt line 271, ":flatten():type(\"xlsx\")") need a string
    # argument to GATE a candidate list in name_one, not just read the
    # value off an already-matched version in name_three. ":type()" is
    # the sole member of compendium 6.7's own "type" functional group,
    # so this is its own retrieve/select duality, same shape as the
    # "uuid"/"name"/"fingerprint" groups already built -- just GATE-
    # only here (no bare-selector form; one file can legitimately have
    # several versions sharing the same type, so a bare ':type("csv")'
    # narrows a SET, it does not select a single entity the way
    # ':uuid()' does). POSITIONS widened to match -- NAME_ONE is the
    # new GATE position, riding alongside FilesReferenceFinder3.query()
    # 's own implied-'*'/bare-:all()/:flatten()/:groups() candidate-
    # gathering (see FilesReferenceFinder3._extract_gate_field_call()),
    # NAME_THREE is its original, unchanged ordinary field-read
    # position.
    #
    NAME = "type"
    SUMMARY = (
        "The file extension of the resolved named-file version, e.g. "
        "'csv', 'xlsx'. An optional string argument GATES a candidate "
        "list in name_one by this field (e.g. ':type(\"csv\")', "
        "':flatten():type(\"xlsx\")')."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "type",
    }
    POSITIONS = {Reference3.FILES: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
