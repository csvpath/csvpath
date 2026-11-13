import re

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.xlsx.xlsx_reader_helper import XlsxReaderHelper

from .functions.function_3 import Function3
from .functions.reference_function_factory_3 import ReferenceFunctionFactory
from .functions.values.time_window_function_3 import TimeWindowFunction3
from .reference_3 import FunctionCall3, Reference3, Star3
from .reference_exceptions_3 import ReferenceException3
from .reference_finder_3 import ReferenceFinder3
from .reference_results_3 import ReferenceResult3, ReferenceResults3


class FilesReferenceFinder3(ReferenceFinder3):
    #
    # first pass, deliberately narrow:
    #  - root_major is a literal named-file name, or "*" (every named-
    #    file). "*" has two exceptions carved out before general
    #    traversal (Rule 1a/1b, a bare/ordinal-indexed :manifest() reads
    #    the global arrivals ledger, see _pointer_before_manifest); any
    #    other use of "*" goes through _query_star_traversal(), which
    #    implements the spec's flatten (bare '*'/path narrowing, pooled
    #    and reduced by one pointer) vs. group (bare ':all()', one
    #    result per named-file+path pair) semantics -- deliberately
    #    narrow itself: combining '*' traversal with :manifest()/a
    #    field-accessor function is not yet supported, see that
    #    method's own docstring.
    #  - name_one is "*", a literal path segment, :name("...") (for a
    #    literal name containing characters -- e.g. a real filename's
    #    "." -- that cannot appear in a bare PATH_SEGMENT), a bare
    #    ':all()', a bare ':flatten()', or a bare ':groups()' -- the
    #    last three settled/corrected 2026-08-12, kept deliberately in
    #    lockstep with ResultsReferenceFinder3's own depth vocabulary
    #    (David: keep functions meaning the same thing across datatypes
    #    wherever the underlying structure supports it -- FILES has the
    #    same "variable, not-known-in-advance path depth" structure
    #    RESULTS does). Full 2x2 depth matrix: ':all()' is a one-level
    #    GROUP, an exact peer of '*' (one-level POOL) -- same [Star3()]
    #    pattern, partitioned by file_home and reduced independently per
    #    partition instead of pooled. ':flatten()' is the any-depth POOL
    #    peer -- every distinct file_home under this name, at any depth,
    #    into ONE pooled answer. ':groups()' is the any-depth GROUP peer
    #    -- same any-depth candidate set as ':flatten()', but partitioned
    #    by file_home like ':all()', reaching each distinct path's own
    #    latest version even when a name's paths do not all sit at the
    #    same depth (the case that originally motivated this whole
    #    depth-matrix pass). ':all()'/':groups()' (both GROUP) combined
    #    with :manifest()/a field-accessor function is not yet supported
    #    (same under-specified-interaction reasoning as
    #    ResultsReferenceFinder3's own ':all()' restriction) --
    #    ':flatten()' (POOL) has no such restriction here, since
    #    root_major is always known at this position (unlike '*'
    #    traversal below). Any other function-valued segment (e.g.
    #    :quarter()) and the "#worksheet" marker (name_two) are not yet
    #    supported.
    #  - name_three, if present, must resolve to exactly one pointer
    #    function (:first()/:last()/:index(n)) -- matching the
    #    STRUCTURE table: name_one picks *which file*, name_three picks
    #    *which version*. A literal name_three body -- e.g.
    #    "$acme.files.orders.a28b1105c..." -- is ALSO now supported
    #    (added 2026-09-22, closing the deferred-work bucket list gap of
    #    the same name), per compendium 3.19b/3.20's own rule: a literal
    #    string in name_three names the FINGERPRINT of the version. Finds
    #    the one already-name_one-matched candidate whose own
    #    "fingerprint" field equals the literal (no match: empty
    #    results, not an error, same "no match" convention every other
    #    literal-identity lookup in this codebase already uses) -- this
    #    is a MATCH, not an ordinal, so it is handled as its own case
    #    rather than routed through _apply_pointer(). Scoped to the
    #    literal-root query() only, matching the same scoping discipline
    #    as the recent '#worksheet'-combined-with-'*'-traversal note
    #    below -- '*' traversal's own literal-body rejection is
    #    untouched. A literal body combined with trailing functions
    #    (e.g. a hypothetical "orders.a28b1105c...:manifest()") is also
    #    not yet supported -- no worked example demonstrates that shape,
    #    so it stays a clear rejection rather than a guess. ":manifest()"
    #    may ride alongside the pointer (e.g. ":last():manifest()" --
    #    the matched version's own manifest entry) or appear alone with
    #    no pointer at all (e.g. ":manifest()" alone -- every matching
    #    version's entry, unreduced) -- it never narrows/selects itself,
    #    see functions/manifest_3.py. ":all()" is also legal in
    #    name_three -- settled 2026-08-12, mirroring CSVPATHS' own
    #    ":all()" precedent exactly (it is not a POINTER, so its whole
    #    effect is simply NOT reducing -- "$alpha.files.:name(...).
    #    :all()" gives every matched version, unreduced, with real
    #    paths/uuids -- unlike name_three being absent entirely, which
    #    dedupes to directory-level results with uuid=None instead).
    #    ":from()'/':to()' (added 2026-08-13, David: rewind/replay and
    #    comparing versions) window the ordered VERSION list the same
    #    way a pointer does -- "the last N versions"/"version M through
    #    N," unreduced unless a real pointer also rides alongside it (it
    #    then reduces the RANGE, not the full candidate set). Two modes,
    #    picked by each bound's own value type: index-mode (int/
    #    :index(n)) POSITIONALLY slices; date-mode (str/:date(...),
    #    broadened from RESULTS-only 2026-08-13 -- a named-file
    #    version's own registration/load "time" is a real arrival-date
    #    concept, same as RESULTS' run start time) FILTERS by each
    #    version's own "time" manifest field. Mixing modes in one pair
    #    is rejected. Combining with ':all()'/':groups()' grouping in
    #    name_one applies the range/time-window WITHIN each distinct
    #    file_home independently, the same as a plain pointer already
    #    does in GROUP mode (built 2026-10-21 -- see query()'s own
    #    _narrow() docstring; GROUP mode's defining feature is "reduce
    #    per partition," so a range follows that same convention, not a
    #    pooled-then-sliced one).
    #    name_three is
    #    optional: when absent, name_one alone is a prefix search that
    #    returns zero or more paths to file-home directories (one per
    #    distinct file matched, deduplicated across versions) -- per
    #    "creating references v3.txt"'s "Query Vs. Resolve" section.
    #    These directory-level results carry uuid=None: a directory
    #    isn't a specific registered version, so it has no uuid of its
    #    own in the manifest schema.
    #
    # storage facts this relies on (confirmed against FileManager/
    # FileRegistrar and a real manifest.json, not assumed): a named-
    # file's manifest.json is one flat, append-only JSON array covering
    # every version of every distinct file ever registered under that
    # name. Each entry's "file_home" is the directory shared by every
    # version of the same logical file; arrival order is simply array
    # order (not sorted by the "time" field).
    #
    DEFINITION_OWNER = "named-file"
    # uuid -> (name, entry) of the live manifests, per query()/resolve
    # call; see _live_index()
    _live_entries = None

    def _definition_names(self) -> list:
        return self.source.file_names()

    def _definition_home(self, name: str) -> str:
        return self.csvpaths.file_manager.named_file_home(name)

    def _definition_config(self, name: str):
        return self.csvpaths.file_manager.describer.get_config(name)

    def query(self) -> ReferenceResults3:
        # the live entries are read at most once per call (_live_index())
        self._live_entries = None
        reference = self.ref.parsed
        log_results = self._query_log_call(reference)
        if log_results is not None:
            return log_results
        root_major = reference.root_major
        if isinstance(root_major, Star3):
            status_chain = self._bare_status_gate_chain(reference.name_one)
            if status_chain is not None:
                # every named-file at once -- added 2026-10-18, the
                # normative doc's own exact worked example ("select
                # named-files registrations for orders that failed").
                # No per-name filter at all here, unlike the literal-
                # root case above. Since 2026-11-01 only the ledger
                # entries of live versions are candidates: a bare '*'
                # read searches each live named-file in turn, and only
                # ':manifest()' reaches the whole ledger, failures and
                # deleted versions included (compendium 6.19, agreed
                # with David). status itself is read from the ledger,
                # the only place it is written.
                return self._query_status_gate(
                    reference=reference,
                    status_chain=status_chain,
                    names=self.source.file_names(),
                )
            if self._is_bare_pointer_reference(reference, "manifest"):
                # Rule 1a (manifest_field_functions_proposal.md): "*" at
                # root_major combined with a bare :manifest() is the one
                # exception -- it resolves to the Named-File Arrivals
                # Manifest, a single global ledger at the named-files
                # root tracking every arrival across every named-file
                # (see files_listener.py). :definition() has no
                # equivalent global resource, so it stays unsupported
                # here, same as any other function.
                home = self.csvpaths.config.inputs_files_path
                return self._query_well_known_file(home, "manifest.json")
            pointer_call = self._pointer_before_manifest(reference, "manifest")
            if pointer_call is not None:
                # Rule 1b -- a pointer riding before the bare :manifest()
                # (e.g. "$*.files.:last():manifest()") selects one entry
                # out of the global ledger by ordinal position, instead
                # of dumping the whole thing.
                return self._query_ledger_pointer(
                    pointer_call=pointer_call, name_filter=None
                )
            return self._query_star_traversal(reference)

        if isinstance(root_major, FunctionCall3):
            # :regex()/:choice() at root_major -- :regex() added
            # 2026-08-27, :choice() added 2026-10-20 (ChoiceSelector3's
            # own .pattern property already compiles down to an
            # equivalent anchored regex alternation, so it is built and
            # used identically from here on). Structurally identical to
            # the Star3 case just above (every named-file is a
            # candidate), just pre-filtered by pattern before
            # _query_star_traversal() enumerates -- see its own
            # name_filter docstring. No other function is legal here;
            # the grammar itself is permissive (any function, see
            # reference_grammar_3.py's own note) so this is a semantic
            # check, not a grammar-level one.
            if root_major.name not in ("regex", "choice"):
                raise ReferenceException3(
                    f":{root_major.name}() is not a legal root_major "
                    "function -- only :regex()/:choice() are supported."
                )
            built = self._build(root_major)
            status_chain = self._bare_status_gate_chain(reference.name_one)
            if status_chain is not None:
                # the bare status gate on the live versions of the matching
                # named-files, as for '*' above (6.13b(iv): a filtered
                # '*'). It raised "field functions attached directly to
                # name_one" until 2026-11-12.
                return self._query_status_gate(
                    reference=reference,
                    status_chain=status_chain,
                    names=self._matching_names(
                        self.source.file_names(), built.pattern
                    ),
                )
            pointer_call = self._pointer_before_manifest(reference, "manifest")
            if pointer_call is not None:
                # Rule 1b on the ledger set filtered by name (6.13b), as
                # for '*' above. It raised "Does not yet support
                # :manifest() as a name_one path segment" until
                # 2026-11-12. A bare ':manifest()' here is still not
                # supported (decision log W1).
                return self._query_ledger_pointer(
                    pointer_call=pointer_call, name_filter=built.pattern
                )
            return self._query_star_traversal(reference, name_filter=built.pattern)

        name_one = reference.name_one
        if (
            name_one.name_two is not None
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name not in ("name", "regex", "choice")
        ):
            # '#worksheet' only means anything against a literal named-
            # file path (there is one specific file to have worksheets
            # in) -- ':name("...")'/':regex(...)'/':choice(...)' are all
            # path-BUILDING (a literal name, a pattern match, or an
            # exact-match alternation, added 2026-09-23 for
            # ':regex()' -- same reasoning), same as any other literal
            # path segment, so both are exempt here same as they are
            # from _is_bare_function_only's own "bare marker" test; a
            # bare context-setter/pointer/marker function occupying
            # name_one's entire content (':manifest()', ':all()',
            # ':flatten()', etc.) has no file of its own to read a
            # worksheet from.
            raise ReferenceException3(
                "FilesReferenceFinder3 does not support the '#worksheet' "
                "marker (name_two) combined with a bare context-setter/"
                "pointer function in name_one -- it only applies to a "
                "literal named-file path."
            )

        status_chain = self._bare_status_gate_chain(name_one)
        if status_chain is not None:
            # a literal root narrows the global ledger to just this
            # name -- added 2026-10-18, David: "if you were inspecting
            # a run that should have happened overnight you would know
            # what status you were looking for... in many cases we
            # know those high risk files by name" -- confirmed just as
            # real a need as the '*' form below, built together. Only
            # the ledger entries of this named-file's live versions are
            # candidates (2026-11-01, as for '*' above).
            ledger = self._live_ledger_entries(names=[root_major])
            by_name = [e for e in ledger if e.get("named_file_name") == root_major]
            matched = self._filter_ledger_by_gate_chain(by_name, status_chain)
            if reference.name_three is not None:
                return self._pointer_into_status_matches(reference, matched)
            return ReferenceResults3(
                results=[
                    ReferenceResult3(
                        path=self._ledger_entry_result_path(e), uuid=e.get("uuid")
                    )
                    for e in matched
                ]
            )

        if self._is_bare_pointer_reference(
            reference, "manifest"
        ) or self._is_bare_pointer_reference(reference, "definition"):
            # both ":manifest()" and ":definition()" are a bare, sole-
            # content name_one whose function name IS the JSON file's
            # own name (manifest.json/definition.json) -- see
            # _query_well_known_file() on the ABC.
            home = self.csvpaths.file_manager.named_file_home(root_major)
            filename = f"{name_one.path[0].name}.json"
            return self._query_well_known_file(home, filename)

        if self._is_bare_pointer_reference(reference, "readme"):
            # ":readme()" -- added 2026-09-21, same bare-content shape
            # as :manifest()/:definition() above, but README.md is not
            # a ".json"-suffixed name, so it gets its own branch rather
            # than joining the generic f"{name}.json" construction.
            home = self.csvpaths.file_manager.named_file_home(root_major)
            return self._query_well_known_file(home, "README.md")

        manifest_chain = self._manifest_chain(name_one=name_one)
        if manifest_chain is not None:
            # a general chain on ':manifest()', e.g.
            # ':manifest():last():uuid()' -- finding E, 2026-11-02. Ahead
            # of the #410 branch below, which used to take
            # ':status("complete"):manifest()' for a path and ignore the
            # gate.
            return self._query_manifest_chain(
                reference=reference, chain=manifest_chain, name_filter=None
            )

        definition_calls = self._definition_chain(name_one=name_one)
        if definition_calls is not None:
            # ':definition()' with fields, e.g. ':definition():on_arrival()'
            # or ':definition(:on_arrival(:has_value()))' (compendium 6.19,
            # E3, 2026-11-02).
            return self._query_definition_chain(
                reference=reference, calls=definition_calls, name_filter=None
            )

        manifest_field_call = self._bare_manifest_field_call(name_one)
        if manifest_field_call is not None:
            # ':manifest():uuid()'/':manifest():time()' -- added
            # 2026-08-28, David's own worked example ("get all acme
            # registration uuids"). Maps the chained field over EVERY
            # entry in this named-file's own manifest.json, one
            # ReferenceResult3 per entry -- resolve()'s existing
            # per-result "for result in results.results: result.data =
            # self._extract_data(result)" loop already turns N results
            # into N resolved values for free (confirmed by reading it
            # before building this, see reference_finder_3.py's own
            # resolve_from()), so no new resolution machinery is needed
            # at that layer, only here (producing N real results) and
            # in _extract_data() (reading the field per result).
            if reference.name_three is not None:
                # settled, not a gap (not-yet-supported sweep #2):
                # resolve_kind's own terminal_functions property reads
                # ONLY name_three.functions once name_three is present
                # (see reference_3.py's own docstring), so a name_three
                # pointer riding alongside this bare chain (e.g.
                # ":manifest():uuid().:last()") would silently DROP the
                # ":uuid()" field intent and resolve to raw file bytes
                # instead -- confirmed by tracing resolve_kind/
                # _extract_data before rejecting this, not assumed.
                # Correctly expressing "pointer, then field" already
                # has its own, unambiguous shape (e.g. ":last():uuid()",
                # see normative_reference_examples.txt line 1001) -- no
                # worked example asks for the field-then-pointer
                # ordering this would add, and building it would need
                # resolve_kind itself to change first.
                raise ReferenceException3(
                    f"FilesReferenceFinder3 does not support combining a "
                    f"bare ':manifest():{manifest_field_call.name}()' lookup "
                    "with name_three -- it already reads a field from every "
                    "matched entry on its own; put the pointer first "
                    f"instead (e.g. ':last():{manifest_field_call.name}()')."
                )
            manifest = self.source.file_manifest(root_major)
            manifest = self._filter_by_manifest_chain_gate(
                reference=reference, call=manifest_field_call, entries=manifest
            )
            path = self._root_manifest_path(root_major)
            # an argued field is a gate: it supplies no value, so resolve
            # gives whole entries, and several at once is a Rule 1 read
            # (2026-11-08), as ':name("x").:manifest():type("csv")' is
            return ReferenceResults3(
                results=[ReferenceResult3(path=path, uuid=e["uuid"]) for e in manifest],
                ambiguous_content_read=(
                    manifest_field_call.arg is not None and len(manifest) > 1
                ),
            )

        pointer_call = self._pointer_before_manifest(reference, "manifest")
        if pointer_call is not None:
            # symmetry fix, added 2026-10-16: the literal-root_major
            # counterpart to Rule 1b above (a pointer riding alongside a
            # bare ':manifest()' call, in either order, ordinal-selects
            # one entry) -- here against THIS named-file's own
            # manifest.json instead of the global ledger. Closes a real
            # consistency gap: CSVPATHS/RESULTS already support this
            # exact bare-chain shape natively (name_one there is always
            # a function chain, never a literal path), confirmed live
            # before building this (David, 2026-10-15/16) via a working
            # "$acme.csvpaths.:manifest():last()" repro; FILES alone
            # lacked it because name_one is NORMALLY a path there, with
            # :manifest()/:definition() carved out as the only non-path
            # exceptions (_is_bare_pointer_reference, just above). Not a
            # wildcard/pooling concern -- FILES has no implied-'*' wiring
            # at all (see _apply_implied_star's own docstring), and even
            # once it did, :manifest() is an explicit, named exemption
            # from that mechanism (fixed 2026-10-15, #376) precisely
            # because a pointer alongside it means "ordinal-index into
            # the one array the REST of the chain already identifies,"
            # not "match a wildcarded path."
            manifest = self.source.file_manifest(root_major)
            selected = self._apply_pointer(pointer_call, manifest)
            if selected is None:
                return ReferenceResults3(results=[])
            path = self._root_manifest_path(root_major)
            return ReferenceResults3(
                results=[ReferenceResult3(path=path, uuid=selected["uuid"])]
            )

        field_call = self._extract_gate_field_call(name_one)
        name_one_pointer = None
        name_one_manifest = None
        if reference.name_three is None:
            name_one_pointer = self._name_one_pointer(name_one)
            if name_one_pointer is None:
                name_one_manifest = self._name_one_manifest_call(name_one)
        if (
            name_one.functions
            and name_one_pointer is None
            and name_one_manifest is None
        ):
            # settled, not a gap (not-yet-supported sweep #3): the
            # compendium's own STRUCTURE table draws this exact line --
            # name_one picks WHICH file, name_three picks WHICH version
            # -- and no worked example anywhere chains a version-
            # selecting function directly onto a literal path with no
            # separating "." (every one either uses name_three, or uses
            # a path-BUILDING function like :name()/:regex() exempted
            # above). This is restating the design, not deferring it.
            raise ReferenceException3(
                self._attached_functions_message(
                    name_one=name_one, star_traversal=False
                )
            )
        # bare ':all()'/':flatten()'/':groups()' for ONE named-file --
        # see the class docstring's 2026-08-12 note. ':all()' is a
        # one-level GROUP, exactly the pattern '*' already matches, just
        # partitioned by file_home and reduced per-partition below
        # instead of pooled. ':flatten()'/':groups()' both match at ANY
        # depth (the real gap a literal/'*' pattern cannot reach, an
        # exact segment count) -- ':flatten()' pools that any-depth set
        # into one answer, ':groups()' partitions it by file_home like
        # ':all()' does, just over the any-depth set instead of the
        # one-level one.
        is_grouped = self._is_bare_all_reference(name_one)
        is_flattened = self._is_bare_flatten_reference(name_one)
        is_deep_grouped = self._is_bare_groups_reference(name_one)
        partitioned = is_grouped or is_deep_grouped
        if is_grouped:
            candidates = self._candidates_for_name(root_major, [Star3()])
        elif is_flattened or is_deep_grouped:
            candidates = self._all_candidates_for_name(root_major)
        elif self._is_bare_selector_reference(name_one):
            # bare ':fingerprint("hash...")' -- added 2026-08-13, the
            # shape generalized 2026-08-28 (see Function3.
            # SELECTOR_WHEN_ARGUED/ReferenceFinder3.
            # _is_bare_selector_reference() -- Fingerprint3 is still the
            # only function that declares it, so behavior here is
            # unchanged, just no longer hand-written to the literal name
            # "fingerprint"). Content-hash identity does not care which
            # file/path slot a version happens to be registered under
            # (unlike ':name()', which matches file_home, a path
            # identity, not a content one), so this searches the WHOLE
            # named-file's manifest directly -- every file_home/path,
            # not just a pattern-matched subset -- for the entry whose
            # own field (this function's own KEY) matches. Confirmed
            # against FileRegistrar's real write path: the version file
            # itself is literally stored/named by its own fingerprint,
            # so an exact match here is reliable. At most one match is
            # expected in practice (two DIFFERENT logical files sharing
            # byte-identical content is the only way to get more than
            # one) -- not specially guarded against.
            #
            # Returns the matched version(s) directly, with their real
            # path/uuid, and does NOT fall through to the shared "no
            # name_three -> dedupe to a directory, uuid=None" logic below
            # -- unlike ':name()', a fingerprint already identifies one
            # SPECIFIC version, there is no further "which version"
            # narrowing step to defer. name_three combined with this
            # shape is settled, not a gap (not-yet-supported sweep #2):
            # redundant by construction (a content-hash match is already
            # 0-or-1 results, nothing left for a pointer to narrow), and
            # a field accessor would hit the identical resolve_kind
            # pitfall ':manifest():field()'+name_three does just above
            # (terminal_functions reads only name_three.functions once
            # name_three exists, silently dropping this bare selector's
            # own field intent).
            call = name_one.path[0]
            if reference.name_three is not None:
                raise ReferenceException3(
                    f"FilesReferenceFinder3 does not support combining "
                    f"a bare ':{call.name}(...)' lookup with name_three -- "
                    "it already identifies one specific version on its own."
                )
            function_cls = ReferenceFunctionFactory.get_registered_class(call.name)
            key = function_cls.KEY.get(Reference3.FILES)
            manifest = self.source.file_manifest(root_major)
            value = call.arg
            matched = [e for e in manifest if e.get(key) == value]
            return ReferenceResults3(
                results=[
                    ReferenceResult3(path=e["file"], uuid=e["uuid"]) for e in matched
                ]
            )
        elif self._is_flatten_prefixed_reference(name_one):
            # ':flatten()' as name_one's FIRST segment, followed by more
            # path -- settled 2026-08-12, David: "the last version of
            # all orders.csv no matter how many template levels from 0
            # to n" ($alpha.files.:flatten()/:name("orders.csv").:last()).
            # The mirror image of RESULTS' own prefixed ':flatten()'
            # (literal-prefix, THEN any depth) -- here the any-depth
            # part comes first and a fixed literal/'*'/:name(...) suffix
            # pattern (everything after it) anchors the end. Matches ANY
            # number of segments, including zero, before that suffix --
            # same "any depth, including a direct/zero-level match"
            # convention bare ':flatten()' already uses.
            if name_one.path[0].arg is not None:
                raise ReferenceException3(
                    "FilesReferenceFinder3's ':flatten()' does not take an "
                    "argument."
                )
            suffix_pattern = self._compile_path_pattern(name_one.path[1:])
            candidates = self._candidates_for_name_by_suffix(root_major, suffix_pattern)
        elif self._is_prefixed_flatten_reference(name_one):
            # a literal/'*'/:name(...) PREFIX, THEN ':flatten()' at some
            # OTHER position (not first -- that's the elif above), THEN
            # an OPTIONAL literal/'*'/:name(...) SUFFIX -- built
            # 2026-08-27, closing the gap deferred 2026-08-12 (David
            # wants it eventually: "any orders.csv below 2025, at any
            # depth in between," e.g. "2025/:flatten()/:name('orders.csv')").
            # Purely additive, as originally scoped -- does not touch the
            # bare or ':flatten()'-first shapes above, and only reachable
            # when ':flatten()' is neither name_one's only segment nor
            # its first one. A missing suffix (e.g. "2025/:flatten()"
            # alone) falls out of the same matcher for free -- "prefix,
            # then any depth, no further constraint" -- same "empty
            # pattern is legal" convention _candidates_for_name(name, [])
            # already uses elsewhere in this file, not a special case
            # needing its own guard.
            flatten_index = next(
                i
                for i, seg in enumerate(name_one.path)
                if isinstance(seg, FunctionCall3) and seg.name == "flatten"
            )
            if name_one.path[flatten_index].arg is not None:
                raise ReferenceException3(
                    "FilesReferenceFinder3's ':flatten()' does not take an "
                    "argument."
                )
            prefix_pattern = self._compile_path_pattern(name_one.path[:flatten_index])
            suffix_pattern = self._compile_path_pattern(
                name_one.path[flatten_index + 1 :]
            )
            candidates = self._candidates_for_name_by_prefix_and_suffix(
                root_major, prefix_pattern, suffix_pattern
            )
        else:
            # compendium 3.9c/3.9d: a function starting name_one or
            # following directly after a path separator implies a '*'
            # wildcard, unless it is itself a wildcard, fully occupies a
            # path segment (:name()/:regex()/a clock function), or does
            # not operate in a path segment at all -- all already
            # excluded by the branches above (bare/prefixed :all()/
            # :flatten()/:groups()/selector-when-argued) or by
            # _apply_implied_star()'s own exemption list (:name()/
            # :regex()/a clock function, checked again here since this
            # branch is also reached by a literal-PREFIXED path ending in
            # one of those, e.g. "orders/:name(...)", not just a bare
            # one). Added 2026-10-16, closing the gap the "implied-'*'
            # wildcard" bucket-list entry's own direction-functions
            # follow-up flagged: a not-otherwise-recognized function
            # landing here (e.g. ":after()", declared name_three-only for
            # FILES) used to reach _compile_path_pattern() directly and
            # raise a misleading "not a legal name_one path segment"
            # error, DIFFERENT from the "functions attached directly to
            # name_one" error the identical, already-normalized explicit-
            # '*' form raises just above (line 292) -- the spec says both
            # forms should parse to the SAME shape, so they must fail
            # with the SAME reason too. Safe to call unconditionally
            # here, not a regression risk the way an EARLIER insertion
            # point was (David, 2026-09-24, broke 29 tests by running
            # this before the dedicated bare-shape checks had their own
            # turn): every branch above this one already required
            # `name_one.functions` to be empty to even be considered (see
            # each one's own docstring), and the blanket raise at line 292
            # already intercepts anything that reached here with
            # `name_one.functions` non-empty from the grammar directly --
            # so by construction, `name_one.functions` is guaranteed
            # empty on entry to this `else`, and the only way
            # `_apply_implied_star()` can populate it is its own
            # documented mutation, which no earlier branch's own
            # recognized shape is exposed to (none of them reach this
            # `else` at all once matched).
            self._apply_implied_star(name_one)
            if field_call is None:
                # the bare/prefixed implied-star shapes (e.g. ':type(
                # "csv")', 'orders/:type("csv")') only populate
                # name_one.functions via _apply_implied_star()'s own
                # mutation just above -- the earlier extraction
                # attempt (before this branch) necessarily found
                # nothing yet, since the function was still sitting in
                # name_one.path at that point, not .functions.
                field_call = self._extract_gate_field_call(name_one)
            if reference.name_three is None:
                if name_one_pointer is None:
                    name_one_pointer = self._name_one_pointer(name_one)
                if name_one_pointer is None and name_one_manifest is None:
                    name_one_manifest = self._name_one_manifest_call(name_one)
            if (
                name_one.functions
                and name_one_pointer is None
                and name_one_manifest is None
            ):
                # same settled restriction as the literal-root branch
                # above (not-yet-supported sweep #3) -- just reached via
                # the implied-'*' normalization instead of a direct
                # literal path, e.g. "orders/:after(...)".
                raise ReferenceException3(
                    self._attached_functions_message(
                        name_one=name_one, star_traversal=False
                    )
                )
            pattern = self._compile_path_pattern(name_one.path)
            candidates = self._candidates_for_name(root_major, pattern)

        if field_call is not None:
            # compendium 3.9d's own GATE, added 2026-10-18 -- e.g.
            # ':type("csv")'/'*:type("csv")'/':flatten():type("xlsx")'
            # (normative_reference_examples.txt line 271) all converge
            # here regardless of which branch above built `candidates`,
            # same "filter before any grouping/reduction" composition
            # RESULTS'/CSVPATHS' own GATE mechanisms already use.
            key = field_call.KEY.get(Reference3.FILES)
            candidates = [
                c
                for c in candidates
                if self._matches_field_predicate(c.get(key), field_call.arg)
            ]

        name_three = reference.name_three
        if name_three is None:
            if name_one_pointer is not None and name_one.name_two is not None:
                # not yet supported -- a worksheet read means content
                # (the sheet's own rows), not a manifest entry, which
                # is what the "name_one, file pointer" shape below
                # resolves to. No worked example asks for this
                # combination, so it is rejected explicitly rather than
                # silently giving the (probably unwanted) manifest
                # entry instead of sheet content.
                raise ReferenceException3(
                    "FilesReferenceFinder3 does not yet support a version-"
                    "selecting pointer directly in name_one (e.g. ':last()') "
                    "combined with the '#worksheet' marker (name_two) -- put "
                    "the pointer in name_three instead."
                )
            if name_one_manifest is not None and name_one.name_two is not None:
                # not yet supported -- no worked example asks for a
                # worksheet read alongside a bare, name_one-narrowed
                # ':manifest()' (which resolves to manifest entries,
                # not file content), so rejected explicitly rather
                # than silently giving the wrong kind of result.
                raise ReferenceException3(
                    "FilesReferenceFinder3 does not yet support a bare "
                    "':manifest()' directly in name_one combined with the "
                    "'#worksheet' marker (name_two) -- put the manifest "
                    "read in name_three instead."
                )
            if name_one_pointer is not None:
                # compendium 5.21's "name_one, file pointer" shape --
                # the pointer already narrowed `candidates` (filtered
                # by field_call above, if any) to the one manifest
                # entry it selects, same ordinal lookup
                # _pointer_before_manifest's own explicit ':manifest()'+
                # pointer shape already uses.
                selected = self._apply_pointer(name_one_pointer, candidates)
                if selected is None:
                    return ReferenceResults3(results=[])
                return ReferenceResults3(
                    results=[
                        ReferenceResult3(
                            path=selected["file"], uuid=selected["uuid"]
                        )
                    ]
                )
            if name_one_manifest is not None:
                # issue #410 -- a bare ':manifest()' chained after a
                # real name_one narrowing prefix (e.g. ':name(
                # "food.csv")') maps the manifest ENTRY over every
                # candidate that prefix matched, analogous to
                # _bare_manifest_field_call()'s own "map a field over
                # every entry" shape but with no field to drill into.
                path = self._root_manifest_path(root_major)
                return ReferenceResults3(
                    results=[
                        ReferenceResult3(path=path, uuid=c["uuid"])
                        for c in candidates
                    ]
                )
            if name_one.name_two is not None:
                raise ReferenceException3(
                    "FilesReferenceFinder3 requires a version-selecting "
                    "pointer (:first()/:last()/:index(n)) alongside the "
                    "'#worksheet' marker (name_two) -- there is no single "
                    "version to read a worksheet from otherwise."
                )
            file_homes = []
            for entry in candidates:
                if entry["file_home"] not in file_homes:
                    file_homes.append(entry["file_home"])
            return ReferenceResults3(
                results=[
                    ReferenceResult3(path=file_home, uuid=None)
                    for file_home in file_homes
                ]
            )

        if isinstance(name_three.body, str):
            # a literal name_three body -- e.g. "orders.a28b1105c..." --
            # names the FINGERPRINT of the version, per compendium
            # 3.19b/3.20. Not a pointer (an ordinal position); a MATCH
            # against the already-name_one-matched candidates' own
            # "fingerprint" field. No match is empty results, not an
            # error -- same convention CSVPATHS'/RESULTS' own literal-
            # identity lookups already use.
            matched = next(
                (c for c in candidates if c.get("fingerprint") == name_three.body),
                None,
            )
            if not name_three.functions:
                # a literal fingerprint body reduces to exactly one
                # version, same as a real pointer would -- the
                # '#worksheet' marker (name_one.name_two, carried
                # through unchanged below) is satisfied by this
                # reduction just as well as by a real POINTER function;
                # no separate check needed here.
                if matched is None:
                    return ReferenceResults3(results=[])
                return ReferenceResults3(
                    results=[
                        ReferenceResult3(
                            path=matched["file"],
                            uuid=matched["uuid"],
                            identity=name_one.name_two,
                        )
                    ]
                )
            # a literal body combined with trailing functions (e.g.
            # ":manifest()"/":uuid()") -- added 2026-10-20 (not-yet-
            # supported sweep #4), closing the gap the old unconditional
            # rejection left. The body already reduces `candidates` to
            # at most one match before any function even runs, same as
            # a real pointer would -- so falling through into the
            # ordinary pointer/manifest/field-accessor machinery below,
            # scoped to just that one candidate (or none), reuses it
            # exactly, rather than duplicating it. Unlike the bare-
            # chain-in-name_one shapes task #2 left unbuilt, there is no
            # resolve_kind conflict here: resolve_kind's own terminal_
            # functions reads name_three.functions regardless of
            # whether name_three ALSO carries a body, so a trailing
            # ':uuid()' is seen and resolved exactly as it would be
            # after a real pointer.
            candidates = [matched] if matched is not None else []
        elif name_three.body is not None:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not support a literal name_three "
                "body of this type -- it must be a string (the version's own "
                "fingerprint) or absent."
            )
        built = self._build_chain(name_three.functions)
        for f in built:
            # replaces the old "at least one recognized category
            # present" gate below (settled 2026-08-14) -- that gate only
            # checked for ABSENCE of every recognized category, it never
            # rejected an individual EXTRA unrecognized function riding
            # alongside a legitimate one (e.g. ":last():name('y')" --
            # confirmed via direct testing this used to silently swallow
            # the stray :name() instead of raising, the same bug class
            # already fixed for CSVPATHS). name_three.functions is
            # guaranteed non-empty here (NameThree3's own constructor
            # requires a body or functions; body is already confirmed
            # None above), so `built` can never be empty either -- every
            # element passing this check already implies "at least one
            # recognized thing," making the old gate's own "nothing
            # recognized at all" case unreachable now, not just
            # redundant.
            self._check_position(f, Reference3.NAME_THREE, Reference3.FILES)
            # an argued ':uuid()'/':fingerprint()' here is a gate, as in
            # RESULTS (David, 2026-11-06; compendium 6.44). It used to be
            # rejected (2026-08-13, generalized 2026-10-18); '*' already
            # filtered by it.
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        gates = [f for f in built if self._is_name_three_gate(f)]
        if name_one.name_two is not None and not pointers:
            raise ReferenceException3(
                "FilesReferenceFinder3 requires a version-selecting "
                "pointer (:first()/:last()/:index(n)) alongside the "
                "'#worksheet' marker (name_two) -- there is no single "
                "version to read a worksheet from otherwise."
            )
        has_manifest = any(f.name == "manifest" for f in built)
        #
        # a gate supplies no value (finding D), so only an unargued field
        # makes a ':manifest()' read a field read.
        #
        has_field_function = any(
            self._find_field_function_call([f]) is not None
            and not self._is_name_three_gate(f)
            for f in built
        )
        has_all = any(f.name == "all" for f in built)
        lower_call, upper_call = self._range_calls_from_built(built)
        has_range = lower_call is not None or upper_call is not None
        from_bound = to_bound = None
        if has_range:
            # ':from()'/':to()' (inclusive) or their exclusive siblings
            # ':after()'/':before()' (compendium 6.28, generalized
            # 2026-10-16 -- see _range_calls_from_built()'s own
            # docstring) as a name_three version range -- added
            # 2026-08-13, David: rewind/replay and version comparison
            # need "the last N versions of orders.csv" the same way
            # RESULTS' own run-level range does, plus "version M through
            # N." Windows the ordered VERSION list of the already
            # name_one-matched file(s), same position :first()/:last()/
            # :index(n) already occupy -- a pointer riding alongside
            # either one reduces the RANGE, not the full candidate set
            # (identical pattern to RESULTS).
            #
            # Two independent MODES, picked by each bound's own value
            # type, same as RESULTS' own run-level range: index-mode
            # (int/:index(n)) POSITIONALLY slices via the shared
            # _apply_range(); date-mode (str/:date(...), broadened from
            # RESULTS-only 2026-08-13 -- David: a named-file version's
            # own registration/load "time" (see functions/fields/
            # time_3.py) is a real arrival-date concept, the same one
            # RESULTS already filters run-level ranges by) FILTERS by
            # each version's own "time" manifest field instead, via the
            # shared _apply_manifest_date_range(). The two modes may mix
            # (6.32) only as a non-negative index lower bound with a date
            # upper bound, where both readings of the index agree; e.g.
            # ":from(:date('2025-01-01')):to(:index(10))" ("10 versions
            # starting from this date"?) still raises, since whether the
            # index counts from the start of the list or from the date
            # anchor is not settled (6.29, 6.30; decision log W4). See
            # ReferenceFinder3._apply_mixed_range().
            from_bound = self._range_bound(lower_call) if lower_call is not None else None
            to_bound = self._range_bound(upper_call) if upper_call is not None else None
            # a TimeWindowFunction3 bound has nothing to validate this
            # way -- never a raw user-supplied string (Date3 already
            # validates its own format at construction); only a bare
            # string bound needs this check.
            if isinstance(from_bound, str):
                self._validate_date_format(from_bound)
            if isinstance(to_bound, str):
                self._validate_date_format(to_bound)
        # Gap 1 of compendium 6.27/TimeWindowFunction3 (added 2026-10-17)
        # -- a BARE time-component function riding in the chain, with
        # no explicit ':from()'/':to()'/':before()'/':after()' of its
        # own (6.27e's first bullet -- the compendium's own flagship
        # example, "$acme.files.:yesterday()"). Detected as its own,
        # separate entry in `built` -- a TimeWindowFunction3 nested as
        # lower_call's/upper_call's own .arg (Gap 2, handled above)
        # never shows up here.
        bare_time_windows = [f for f in built if isinstance(f, TimeWindowFunction3)]
        if len(bare_time_windows) > 1:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not support combining more "
                "than one bare time-component function (e.g. "
                "':yesterday()') in the same name_three chain."
            )
        bare_time_window = bare_time_windows[0] if bare_time_windows else None
        if bare_time_window is not None and has_range:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not support combining a bare "
                "time-component function (e.g. ':yesterday()') with an "
                "explicit ':from()'/':to()'/':before()'/':after()' bound "
                "in the same name_three chain -- the bare function "
                "already means its own whole period, both ends included."
            )
        # the old "at least one recognized category present" gate that
        # used to live here is now unreachable, not just redundant: the
        # _check_position() loop above already guarantees every element
        # of `built` (which is itself guaranteed non-empty, see that
        # loop's own comment) is one of exactly the categories checked
        # below (pointers/has_manifest/has_field_function/has_all/
        # has_range cover the complete set of name_three-legal FILES
        # functions), so at least one of them is always true here.

        # `partitioned and pointers and has_manifest` used to be an
        # unconditional rejection here ("does not yet support combining
        # ':all()'/':groups()' grouping with :manifest()") -- removed
        # 2026-10-16, partition-aware fix (see the bucket list's "'*'-
        # traversal content-accessor guards" entry, done-list writeup
        # for the full reasoning). The reduction logic just below already
        # does exactly the right thing: `partitioned` reduces each
        # distinct file_home's own candidates independently via the
        # pointer BEFORE :manifest()'s own entry (or a field accessor) is
        # ever read, so "several groups, each already reduced to exactly
        # one via its own pointer" is not the same Rule 1 violation as
        # pooling several raw, unreduced candidates sharing one
        # :manifest() read -- it is the identical shape CSVPATHS already
        # ships (`_star_group_and_reduce`'s own `accessor is not None and
        # pointer is not None` handling). `ambiguous_content_read`'s own
        # computation just below is now partition-aware instead of a
        # naive count check, so it correctly distinguishes the two cases
        # rather than this method raising to avoid the ambiguity
        # entirely.

        def _narrow(cands: list) -> list:
            # ':from()'/':to()' (or a bare time-component function) as a
            # name_three version range/window -- applied per-partition
            # in GROUP mode (not-yet-supported sweep #5 follow-up, David:
            # "isn't the path unambiguously Reading B? Wasn't that the
            # point of :groups() being different from :flatten()?") --
            # he's right: GROUP mode's own defining feature, already
            # built and tested for a plain pointer (:first()/:last()/
            # :index(n)), is "reduce independently within each distinct
            # file_home," not "pool everything first." A range is just a
            # multi-valued pointer, the same category of terminal
            # reduction, so it follows the identical convention -- there
            # was never a genuine second reading, just an earlier
            # implementation that applied the range to the pooled list
            # before this fix extended the per-partition treatment to
            # it. Called once on the whole pooled `candidates` list in
            # POOL mode, and once per distinct file_home's own candidate
            # list in GROUP mode -- see the two call sites below.
            #
            # then the gates (finding G, 2026-11-02): a range comes before
            # a filter, whatever the written order (compendium 6.28), and
            # the pointer picks from what is left.
            #
            if bare_time_window is not None:
                cands = self._apply_bare_time_window_to_manifest(
                    cands, bare_time_window
                )
            elif has_range:
                # index and date bounds may mix (6.32)
                cands = self._apply_mixed_range(
                    entries=cands,
                    lower_call=lower_call,
                    upper_call=upper_call,
                    date_filter=self._apply_manifest_date_range,
                )
            return self._filter_by_gates(
                reference=reference, gates=gates, candidates=cands
            )

        if partitioned:
            # one independent reduction per distinct file_home, not one
            # pooled answer across all of them -- mirrors
            # _query_star_traversal's own is_grouped/is_deep_grouped
            # branch, scoped to this one named-file's own candidates
            # instead of every named-file's. The range/time-window (if
            # any) narrows EACH group's own candidates first, then the
            # pointer (if any) reduces that group's own narrowed list --
            # same order _narrow()'s own docstring explains.
            by_file_home = {}
            for entry in candidates:
                by_file_home.setdefault(entry["file_home"], []).append(entry)
            selected_candidates = []
            for file_home in sorted(by_file_home):
                group_candidates = _narrow(by_file_home[file_home])
                if pointers:
                    selected = self._apply_pointer(pointers[0], group_candidates)
                    if selected is not None:
                        selected_candidates.append(selected)
                else:
                    # :all()/:groups() grouping with a range/time-window
                    # but no pointer -- every version each group's own
                    # window matches, unreduced (e.g. David's own worked
                    # example, "$*.files.:groups().:from(0):to(1))" --
                    # "first 2 registrations for each group").
                    selected_candidates.extend(group_candidates)
        else:
            candidates = _narrow(candidates)
            if pointers:
                # a pointer (with or without :manifest() riding alongside
                # it) reduces to one specific version, same as before.
                selected = self._apply_pointer(pointers[0], candidates)
                selected_candidates = [selected] if selected is not None else []
            else:
                # :manifest() alone, no pointer -- every matching version's
                # own manifest entry, unreduced. Resolving full manifest
                # content for more than one entity at once is still illegal
                # (Rule 1, manifest_field_functions_proposal.md's "Entity
                # resolution and pooling" section) -- but query() itself is
                # always allowed to return every match, regardless of
                # accessor (moved 2026-08-26, see the ":path()" retirement/
                # Rule 1 bucket-list entry); it flags the result instead of
                # raising, and ReferenceFinder3.resolve_from() raises only
                # if a caller actually tries to resolve more than one of
                # these at once. Field accessors are exempt from Rule 1
                # entirely (Rule 3, same doc section) -- a scalar field
                # value is cheap to pool, so :uuid() etc. stay poolable
                # across every matched candidate with no pointer at all,
                # same as before.
                selected_candidates = candidates

        #
        # an explicit ':manifest()' names each version's manifest entry,
        # so query() gives the named-file's manifest.json (compendium 5.7).
        #
        manifest_path = self._root_manifest_path(root_major) if has_manifest else None
        return ReferenceResults3(
            results=[
                ReferenceResult3(
                    path=manifest_path or c["file"],
                    uuid=c["uuid"],
                    identity=name_one.name_two,
                )
                for c in selected_candidates
            ],
            # `and not has_field_function` added 2026-09-28 -- confirmed
            # LIVE this was a real bug: ":manifest():uuid()" (a field
            # accessor chained alongside :manifest()) incorrectly set
            # this flag whenever more than one candidate matched, even
            # though Rule 3 exempts field accessors entirely and
            # resolve_kind's own METADATA_FIELD-before-METADATA_FILE
            # priority means :manifest() itself is never actually read
            # as a whole resource in that shape -- only a BARE
            # :manifest() (no field riding with it) is genuine Rule 1
            # territory.
            #
            # `and not (partitioned and pointers)` added 2026-10-16 --
            # partition-aware fix (bucket list's "'*'-traversal content-
            # accessor guards" entry). When `partitioned and pointers`,
            # `selected_candidates` came from the by-file_home reduction
            # above -- each entry is already the SOLE pointer-selected
            # candidate for its own distinct file_home, not several raw
            # candidates sharing one read. Pooling several already-
            # reduced, independently-identified entities' own single
            # manifest entries is not the same ambiguity Rule 1 guards
            # against (that is exactly what the removed rejection just
            # above used to conflate). `partitioned` with no pointer
            # (bare ':all():manifest()'/':groups():manifest()') still
            # pools genuinely unreduced candidates per group, so the
            # naive count check still correctly flags that case --
            # `pointers` being falsy there makes this new term a no-op.
            ambiguous_content_read=(
                has_manifest
                and not has_field_function
                and len(selected_candidates) > 1
                and not (partitioned and pointers)
            ),
        )

    def _query_star_traversal(
        self, reference: Reference3, name_filter: "str | None" = None
    ) -> ReferenceResults3:
        """root_major == "*" -- query across every named-file, not just
        one. `name_filter` (added 2026-08-27, query()'s own :regex()-at-
        root_major branch) restricts every named_file_names enumeration
        below (via ReferenceFinder3._matching_names()) to named-files
        whose own name matches the pattern -- "every named-file whose
        name matches this pattern" is the SAME candidate-gathering '*'
        already does here, just pre-filtered before enumeration, not a
        new traversal mode. None (the default) means every named-file,
        the ordinary '*' case, unchanged. Four distinct semantics,
        corrected/extended 2026-08-12 to
        match ResultsReferenceFinder3's own depth vocabulary exactly
        (David: keep functions meaning the same thing across datatypes):

        - bare '*'/literal path narrowing (POOL, exactly one level):
          every named-file's matching candidates pool into one combined
          list, sorted by each entry's own "time" so a terminal pointer
          means true chronological order across everything, not
          enumeration order.
        - bare ':all()' as name_one's entire content (GROUP, exactly one
          level -- matches the SAME [Star3()] pattern '*' does, NOT any
          depth as an earlier version of this method did): every
          matching candidate across every named-file is partitioned by
          its own "file_home" (already unique per named-file+path, since
          file_home embeds the named-file's name as a path prefix), and
          the terminal pointer is applied independently within each
          group -- one result per (named-file, path) pair, each that
          pair's own last/first/nth version in its own array order (no
          time-sort needed within one already-single-manifest group).
        - bare ':flatten()' as name_one's entire content (POOL, any
          depth): every named-file's candidates AT ANY DEPTH pool into
          one combined list, time-sorted and reduced exactly like the
          '*' case above -- the any-depth counterpart '*' cannot reach
          (an exact segment count).
        - bare ':groups()' as name_one's entire content (GROUP, any
          depth): same any-depth candidate gathering as ':flatten()',
          but partitioned by file_home like ':all()' instead of pooled
          -- one result per (named-file, path) pair regardless of how
          deep that pair's own path happens to be.

        A field accessor (e.g. :uuid()) riding alongside the pointer in
        name_three is supported (narrowed 2026-08-29, matching FILES'
        own literal-root GROUP-mode fix the same day, and RESULTS' own
        long-settled precedent for the identical shape) -- poolable, one
        value per matched candidate, exempt from Rule 1 (manifest_field_
        functions_proposal.md's "Entity resolution and pooling"
        section) the same way it is everywhere else in this file.
        _extract_data() already resolves this correctly for a Star3
        root_major via the global arrivals ledger (added 2026-08-28,
        alongside FILES' own bare ':manifest():field()' shape -- same
        Star3-aware branch, reused here for free since it keys off
        `field_call` generically, not off which grammar position found
        it).

        :manifest() (a whole-resource read, no field riding alongside
        it) is now deferred to `ambiguous_content_read` too (converted
        2026-09-28, was: an unconditional raise) -- `_extract_data()`
        already resolves it correctly for a Star3 root_major via that
        same Star3-aware ledger branch, already used by Rule 1b's own
        ':manifest()'-with-a-global-pointer shape, and GROUP mode
        (':all()'/':groups()') reducing each distinct file_home to AT
        MOST one candidate via `_apply_pointer()` means the final count
        being > 1 can only mean "more than one GROUP's own already-
        individually-legitimate winner" -- the identical shape already
        proven safe to defer rather than raise (see the RESULTS-side fix
        the same day, `_star_group_and_reduce()`'s own docstring, for
        the fuller writeup of this exact reasoning). A separate, real
        bug was caught and fixed in the process, not just this
        conversion: `:manifest()` combined with a CHAINED FIELD
        ACCESSOR (e.g. ':manifest():uuid()') was ALSO being caught by
        the old unconditional check, even though a field accessor is
        exempt from Rule 1 entirely (Rule 3) and was never meant to
        trigger it -- confirmed live before fixing, the identical bug
        also existed in this method's own literal-root twin above.

        bare ':definition()' as name_one's own content -- added
        2026-08-27 (FILES '*' traversal generalization bucket-list
        entry): every named-file's own definition.json, one result per
        named-file, METADATA_FILE (definition.json is never versioned,
        so there is no "which version" left for name_three to narrow --
        combining it with name_three is rejected). A ':definition()'
        chain with fields is E3's _definition_chain branch. ':home()',
        which used to scope this to named-files with a zero-level
        registration, was retired 2026-11-03 (David).
        """
        name_one = reference.name_one
        if name_one.name_two is not None:
            # settled, not a gap (not-yet-supported sweep #6): reading a
            # worksheet means content from exactly ONE specific XLSX
            # file, but '*' traversal by definition matches across
            # every named-file -- no worked example asks for this, and
            # deciding how a pointer-reduced '*' match should interact
            # with a worksheet read is undecided, so this stays a clear
            # rejection rather than a guess (same reasoning the literal-
            # root '#worksheet'-combination rejections elsewhere in this
            # file already use).
            raise ReferenceException3(
                "FilesReferenceFinder3 does not support the '#worksheet' "
                "marker (name_two) during '*' traversal -- it only applies "
                "to a literal named-file path."
            )
        manifest_chain = self._manifest_chain(name_one=name_one)
        if manifest_chain is not None:
            # a general chain on ':manifest()' over the ledger set --
            # finding E, 2026-11-02.
            return self._query_manifest_chain(
                reference=reference, chain=manifest_chain, name_filter=name_filter
            )
        definition_calls = self._definition_chain(name_one=name_one)
        if definition_calls is not None:
            # ':definition()' with fields over each live named-file, e.g.
            # compendium 6.35's '$*.files.:definition(:on_arrival(
            # :has_value()))' (E3, 2026-11-02).
            return self._query_definition_chain(
                reference=reference, calls=definition_calls, name_filter=name_filter
            )
        if self._is_bare_definition_reference(name_one):
            if reference.name_three is not None:
                # settled, not a gap -- definition.json is never
                # versioned (same reasoning as every other :definition()
                # restriction in this file), so there is structurally
                # nothing for name_three to select.
                raise ReferenceException3(
                    "FilesReferenceFinder3 does not support combining "
                    "':definition()' with name_three during '*' traversal "
                    "-- definition.json is not versioned, there is no "
                    "version to select."
                )
            # one definition.json per named-file, flagged when there are
            # several (Rule 1)
            return self._query_definition_files(
                names=self._matching_names(self._definition_names(), name_filter)
            )

        # issue #438: the '*'-traversal counterpart to query()'s own
        # literal-root GATE extraction (line 394 there). ':type()'s GATE
        # was built 2026-10-18 for the literal-root candidate pipeline
        # only -- unlike ':status()' (wired into BOTH root forms the
        # same day), it was never mirrored here, so e.g.
        # "$*.files.:type(\"xlsx\")" fell through to the generic
        # _compile_path_pattern() path below and raised "not yet
        # supported," even though nothing about the GATE mechanism
        # itself is root-specific. Same two-attempt extraction as
        # query()'s own (catches the explicit '*:type("xlsx")' form
        # here; the bare ':type("xlsx")' form is only caught after
        # _apply_implied_star() normalizes it, in the final `else`
        # branch below), and the same universal post-candidate filter
        # (applied once, after this whole if/elif/else chain, regardless
        # of which branch built `candidates`) as query()'s own (line 631).
        # a gate on ':manifest()' (e.g. ':manifest():type("csv")') is
        # left in place for the ':manifest()' branch below to apply to
        # the ledger, as query() does for a literal root.
        field_call = None
        if self._bare_manifest_field_call(name_one) is None:
            field_call = self._extract_gate_field_call(name_one)
        is_grouped = self._is_bare_all_reference(name_one)
        is_flattened = self._is_bare_flatten_reference(name_one)
        is_deep_grouped = self._is_bare_groups_reference(name_one)
        partitioned = is_grouped or is_deep_grouped
        #
        # the named-file of each candidate, by its file_home, for the
        # plain-path branch: a '$*' root groups by named-file (compendium
        # 4.1b), so a pointer or an index range picks within each one.
        # None for the forms that pool (':flatten()') or that already
        # partition by file_home (':all()', ':groups()').
        #
        named_file_of = None
        name_one_pointer = None
        if is_grouped:
            candidates = []
            for name in self._matching_names(
                self.source.file_names(), name_filter
            ):
                candidates.extend(self._candidates_for_name(name, [Star3()]))
        elif is_flattened or is_deep_grouped:
            candidates = []
            for name in self._matching_names(
                self.source.file_names(), name_filter
            ):
                candidates.extend(self._all_candidates_for_name(name))
        elif self._bare_manifest_field_call(name_one) is not None:
            # ':manifest():uuid()' during '*' traversal -- added
            # 2026-08-28, David's own worked example ("get uuids from
            # all registrations"). Reads the global arrivals ledger
            # (Rule 1a's own resource for bare ':manifest()' at '*'
            # root), not each named-file's own manifest -- "every
            # registration across every named-file" is literally what
            # that ledger already tracks, so this stays consistent with
            # Rule 1a rather than reassembling the same set by iterating
            # every name's own manifest. `name_filter` (:regex() at
            # root_major) is applied against each entry's own
            # "named_file_name" field, since the ledger is a flat list,
            # not organized by name the way per-name enumeration is
            # elsewhere in this method.
            manifest_field_call = self._bare_manifest_field_call(name_one)
            if (
                ReferenceFunctionFactory.get_registered_class(
                    manifest_field_call.name
                ).SOURCE
                == "computed"
            ):
                # e.g. ':named_file_home()': computed from the root, which is
                # not a name here. As CSVPATHS does for ':named_paths_home()'
                # (RMF section 4: only with a literal root_major). It raised
                # TypeError before #593, then read each live record's home;
                # reading the ledger's own name_home is decision log W7
                # (2026-11-12).
                raise ReferenceException3(
                    f"FilesReferenceFinder3 does not support "
                    f":{manifest_field_call.name}() combined with '*'/:regex()/"
                    ":choice() traversal -- root_major must be a literal "
                    "named-file name."
                )
            if reference.name_three is not None:
                # settled, not a gap -- the '*' traversal twin of the
                # literal-root restriction query() raises for the same
                # shape (not-yet-supported sweep #2's own writeup):
                # resolve_kind's terminal_functions reads only name_three.
                # functions once name_three exists, so a pointer riding
                # here would silently drop this chain's own field intent.
                raise ReferenceException3(
                    f"FilesReferenceFinder3 does not support combining a "
                    f"bare ':manifest():{manifest_field_call.name}()' lookup "
                    "with name_three during '*' traversal -- it already "
                    "reads a field from every matched entry on its own."
                )
            ledger = self.source.files_ledger()
            #
            # every ledger record, a failed registration included: a
            # failure is tracked only here, and each result's path is the
            # ledger itself, so a failure needs no file. Failures were
            # skipped until 2026-11-01 (agreed with David), when the path
            # was still each arrival's file_path.
            #
            entries = [
                e
                for e in ledger
                if name_filter is None
                or re.search(name_filter, e.get("named_file_name") or "")
            ]
            entries = self._filter_by_manifest_chain_gate(
                reference=reference, call=manifest_field_call, entries=entries
            )
            #
            # ledger records: query() gives the ledger's own path
            # (compendium 5.7).
            #
            path = self._files_ledger_path()
            return ReferenceResults3(
                results=[ReferenceResult3(path=path, uuid=e["uuid"]) for e in entries]
            )
        else:
            # issue #438: mirrors query()'s own identical normalization
            # (lines 599-608) -- a bare field-accessor/GATE function
            # (e.g. ':type("xlsx")') still sits in name_one.path at this
            # point, not .functions, until _apply_implied_star() moves
            # it there; the earlier extraction attempt above necessarily
            # found nothing yet for this shape.
            self._apply_implied_star(name_one)
            if field_call is None:
                field_call = self._extract_gate_field_call(name_one)
            if reference.name_three is None:
                # a lone pointer, e.g. '$*.files.:last()': each named-
                # file's own "name_one, file pointer" (5.21), as the
                # literal root reads '$alpha.files.:last()'
                name_one_pointer = self._name_one_pointer(name_one)
            if name_one.functions and name_one_pointer is None:
                # same settled restriction as query()'s own literal-root
                # branch (not-yet-supported sweep #3), for '*' traversal.
                raise ReferenceException3(
                    self._attached_functions_message(
                        name_one=name_one, star_traversal=True
                    )
                )
            if name_one_pointer is not None and name_one.name_two is not None:
                raise ReferenceException3(
                    "FilesReferenceFinder3 does not yet support a version-"
                    "selecting pointer directly in name_one (e.g. ':last()') "
                    "combined with the '#worksheet' marker (name_two) -- put "
                    "the pointer in name_three instead."
                )
            pattern = self._compile_path_pattern(name_one.path)
            candidates = []
            named_file_of = {}
            for name in self._matching_names(
                self.source.file_names(), name_filter
            ):
                found = self._candidates_for_name(name, pattern)
                for entry in found:
                    named_file_of[entry["file_home"]] = name
                candidates.extend(found)

        if field_call is not None:
            # issue #438: same universal, post-candidate-gathering GATE
            # filter as query()'s own (line 631) -- applies regardless of
            # which branch above built `candidates` (POOL/GROUP/any-depth).
            key = field_call.KEY.get(Reference3.FILES)
            candidates = [
                c
                for c in candidates
                if self._matches_field_predicate(c.get(key), field_call.arg)
            ]

        name_three = reference.name_three
        if name_three is None and name_one_pointer is not None:
            selected_candidates = []
            for group in self._by_named_file(
                candidates=candidates, named_file_of=named_file_of
            ):
                selected = self._apply_pointer(name_one_pointer, group)
                if selected is not None:
                    selected_candidates.append(selected)
            return ReferenceResults3(
                results=[
                    ReferenceResult3(path=c["file"], uuid=c["uuid"])
                    for c in selected_candidates
                ]
            )
        if name_three is None:
            file_homes = []
            for entry in candidates:
                if entry["file_home"] not in file_homes:
                    file_homes.append(entry["file_home"])
            return ReferenceResults3(
                results=[
                    ReferenceResult3(path=file_home, uuid=None)
                    for file_home in file_homes
                ]
            )

        if isinstance(name_three.body, str):
            # literal fingerprint body, now at ANY named-file during
            # '*' traversal -- added 2026-10-20 (not-yet-supported
            # sweep #4), closing the real parity gap the old
            # unconditional rejection here left: the identical literal-
            # root shape (query()'s own "isinstance(name_three.body,
            # str)" branch, just above) already supported this. No
            # time-sort needed first (unlike the pointer-only path
            # below) -- an exact fingerprint match does not care about
            # arrival order. Falls through into the ordinary pointer/
            # manifest/field-accessor machinery below, scoped to the
            # one matched candidate (or none), same reuse the literal-
            # root branch's own trailing-functions fix uses.
            matched = next(
                (c for c in candidates if c.get("fingerprint") == name_three.body),
                None,
            )
            if not name_three.functions:
                if matched is None:
                    return ReferenceResults3(results=[])
                return ReferenceResults3(
                    results=[
                        ReferenceResult3(path=matched["file"], uuid=matched["uuid"])
                    ]
                )
            candidates = [matched] if matched is not None else []
        elif name_three.body is not None:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not support a literal name_three "
                "body of this type -- it must be a string (the version's own "
                "fingerprint) or absent."
            )
        built = self._build_chain(name_three.functions)
        # each must be legal in name_three, as at a literal root: under
        # '*' a ':definition()' here read the version's manifest entry, or
        # a definition field, where the literal form raises (6.13b(iv);
        # reviewer on #593)
        for f in built:
            self._check_position(f, Reference3.NAME_THREE, Reference3.FILES)
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        gates = [f for f in built if self._is_name_three_gate(f)]
        has_manifest = any(f.name == "manifest" for f in built)
        field_call = self._find_field_function_call(built)
        #
        # a gate supplies no value (finding D), so only an unargued field
        # makes a ':manifest()' read a field read.
        #
        has_value_field = any(
            self._find_field_function_call([f]) is not None
            and not self._is_name_three_gate(f)
            for f in built
        )
        # ':from()'/':to()' and a bare time-component function, now
        # supported during '*' traversal too (built 2026-10-21, closing
        # a real gap this method never had at all -- unlike query()'s
        # own literal-root path, which already had full range support,
        # just blocked from combining with grouping until this same
        # fix) -- see this method's own docstring and _narrow()'s own
        # comment for the GROUP-mode-applies-per-partition reasoning.
        lower_call, upper_call = self._range_calls_from_built(built)
        has_range = lower_call is not None or upper_call is not None
        from_is_date = to_is_date = False
        from_bound = to_bound = None
        if has_range:
            from_bound = self._range_bound(lower_call) if lower_call is not None else None
            to_bound = self._range_bound(upper_call) if upper_call is not None else None
            from_is_date = isinstance(from_bound, (str, TimeWindowFunction3))
            to_is_date = isinstance(to_bound, (str, TimeWindowFunction3))
            if isinstance(from_bound, str):
                self._validate_date_format(from_bound)
            if isinstance(to_bound, str):
                self._validate_date_format(to_bound)
        bare_time_windows = [f for f in built if isinstance(f, TimeWindowFunction3)]
        if len(bare_time_windows) > 1:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not support combining more "
                "than one bare time-component function (e.g. "
                "':yesterday()') in the same name_three chain."
            )
        bare_time_window = bare_time_windows[0] if bare_time_windows else None
        if bare_time_window is not None and has_range:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not support combining a bare "
                "time-component function (e.g. ':yesterday()') with an "
                "explicit ':from()'/':to()'/':before()'/':after()' bound "
                "in the same name_three chain -- the bare function "
                "already means its own whole period, both ends included."
            )

        #
        # a '$*' root groups by named-file for a pointer or an index range
        # (compendium 4.1b). A date range or a time window matches each
        # version's own time, so with no pointer it keeps the pooled,
        # time-ordered list.
        #
        # an index bound groups like a pointer (4.1b), mixed with a date
        # bound or not (6.32)
        index_range = (from_bound is not None and not from_is_date) or (
            to_bound is not None and not to_is_date
        )
        by_named_file = named_file_of is not None

        def _narrow(cands: list) -> list:
            # the range or time window, then the gates (finding G,
            # compendium 6.28); the pointer picks from what is left.
            if bare_time_window is not None:
                cands = self._apply_bare_time_window_to_manifest(
                    cands, bare_time_window
                )
            elif has_range:
                # index and date bounds may mix (6.32)
                cands = self._apply_mixed_range(
                    entries=cands,
                    lower_call=lower_call,
                    upper_call=upper_call,
                    date_filter=self._apply_manifest_date_range,
                )
            return self._filter_by_gates(
                reference=reference, gates=gates, candidates=cands
            )

        def _result_path(candidate: dict) -> str:
            # an explicit ':manifest()' names the version's entry in its
            # own named-file's manifest.json (compendium 5.7, 6.13b(iv)).
            if has_manifest:
                return self._named_file_manifest_path(
                    entry=candidate, names=self.source.file_names()
                )
            return candidate["file"]

        if not pointers:
            # a field accessor alone (no pointer) is legal here too --
            # added 2026-09-25, matching the literal-root query()'s own
            # "field accessors are exempt from Rule 1" precedent (a
            # scalar field value is cheap to pool/read per-candidate, no
            # reduction needed to make it meaningful). This method used
            # to reject ANY missing pointer unconditionally, even though
            # the identical literal-root shape already allowed it --
            # confirmed live (David, 2026-09-24) that
            # "$acme.files.:flatten().:uuid()" already worked while
            # "$*.files.:flatten().:uuid()" raised, a real, narrower gap
            # surfaced while investigating FILES' own implied-'*' work
            # (see the bucket list). GROUP mode (`partitioned`) is not
            # specially handled here either, matching literal-root's own
            # uniform "no pointer means every candidate, unreduced"
            # treatment regardless of grouping. A bare ':manifest()'
            # (added 2026-09-28, see below) is ALSO now legal without a
            # pointer, same as it always has been for the literal-root
            # case, and so (added 2026-10-21) is a bare range/time-
            # window -- only "neither a pointer, nor a field accessor,
            # nor :manifest(), nor a range/time-window" is still a
            # genuine "nothing to resolve" rejection.
            if (
                field_call is None
                and not has_manifest
                and not has_range
                and bare_time_window is None
            ):
                raise ReferenceException3(
                    "FilesReferenceFinder3 requires name_three to resolve to "
                    "exactly one pointer function (:first()/:last()/:index(n)) "
                    "when traversing every named-file with '*'."
                )
            if has_range or bare_time_window is not None or gates:
                if partitioned:
                    by_file_home = {}
                    for entry in candidates:
                        by_file_home.setdefault(entry["file_home"], []).append(entry)
                    candidates = []
                    for file_home in sorted(by_file_home):
                        candidates.extend(_narrow(by_file_home[file_home]))
                elif by_named_file and index_range:
                    # an index range is a multi-valued pointer: within each
                    # named-file (4.1b)
                    candidates = [
                        c
                        for group in self._by_named_file(
                            candidates=candidates, named_file_of=named_file_of
                        )
                        for c in _narrow(sorted(group, key=lambda e: e["time"]))
                    ]
                else:
                    candidates = _narrow(sorted(candidates, key=lambda e: e["time"]))
            return ReferenceResults3(
                results=[
                    ReferenceResult3(path=_result_path(c), uuid=c["uuid"])
                    for c in candidates
                ],
                ambiguous_content_read=(
                    has_manifest and not has_value_field and len(candidates) > 1
                ),
            )
        pointer = pointers[0]

        if partitioned:
            by_file_home = {}
            for entry in candidates:
                by_file_home.setdefault(entry["file_home"], []).append(entry)
            selected_candidates = []
            for file_home in sorted(by_file_home):
                group_candidates = _narrow(by_file_home[file_home])
                selected = self._apply_pointer(pointer, group_candidates)
                if selected is not None:
                    selected_candidates.append(selected)
        elif by_named_file:
            selected_candidates = []
            for group in self._by_named_file(
                candidates=candidates, named_file_of=named_file_of
            ):
                narrowed = _narrow(sorted(group, key=lambda e: e["time"]))
                selected = self._apply_pointer(pointer, narrowed)
                if selected is not None:
                    selected_candidates.append(selected)
        else:
            pooled = _narrow(sorted(candidates, key=lambda e: e["time"]))
            selected = self._apply_pointer(pointer, pooled)
            selected_candidates = [selected] if selected is not None else []

        return ReferenceResults3(
            results=[
                ReferenceResult3(path=_result_path(c), uuid=c["uuid"])
                for c in selected_candidates
            ],
            # ':manifest()' (whole-resource, no field riding alongside
            # it) converted 2026-09-28 from an unconditional raise to
            # this deferred pattern -- re-audited against the exact trap
            # the literal-root ':path()'-retirement fix already found
            # once (see ResultsReferenceFinder3._star_group_and_reduce()'s
            # own docstring for the identical reasoning applied there
            # the same day): `partitioned` GROUP mode reduces each
            # distinct file_home to AT MOST one candidate via
            # `_apply_pointer()`, so `len(selected_candidates) > 1` here
            # can only mean "more than one file_home's own already-
            # individually-legitimate winner" -- the same shape already
            # proven safe to defer rather than raise. `_extract_data()`
            # already resolves this correctly for a Star3 root_major via
            # the global arrivals ledger (the same branch Rule 1b's own
            # ':manifest()'-with-a-global-pointer shape already uses),
            # confirmed by reading before relying on it, not assumed.
            #
            # `and not partitioned` added 2026-10-16 -- the comment just
            # above already explains WHY `partitioned` + a pointer is
            # safe (each entry is its own group's already-reduced single
            # winner), but the flag itself did not actually act on that
            # yet -- it still flagged ambiguous whenever more than one
            # named-file's own winner came back, which is every real
            # GROUP-mode `:all():manifest()`/`:groups():manifest()` '*'
            # query with more than one matching named-file. `pointer` is
            # guaranteed present in this branch (the `if not pointers`
            # case above already returned), so no extra truthiness check
            # is needed the way the literal-root fix needed `and pointers`
            # alongside `partitioned`.
            ambiguous_content_read=(
                has_manifest
                and not has_value_field
                and len(selected_candidates) > 1
                and not partitioned
                and not by_named_file
            ),
        )

    @staticmethod
    def _by_named_file(*, candidates: list, named_file_of: dict) -> list:
        """`candidates` split into one list per named-file, in the order
        the named-files were enumerated, each keeping its own order.
        `named_file_of` maps a candidate's file_home to its named-file."""
        if candidates is None:
            raise ValueError("candidates cannot be None")
        if named_file_of is None:
            raise ValueError("named_file_of cannot be None")
        groups = {}
        for entry in candidates:
            groups.setdefault(named_file_of[entry["file_home"]], []).append(entry)
        return list(groups.values())

    def _candidates_for_name(self, name: str, pattern: list) -> list:
        """every manifest entry for one named-file whose file_home
        matches `pattern` relative to that name's own home directory --
        the per-name-file work shared by the literal-root_major path,
        '*' traversal's pool mode, and both ':all()' branches (which
        also match this exact-one-level pattern, just with the results
        partitioned rather than pooled afterward)."""
        manifest = self.source.file_manifest(name)
        home = self.csvpaths.file_manager.named_file_home(name).rstrip("/")
        return [entry for entry in manifest if self._matches(entry, home, pattern)]

    def _candidates_for_name_by_suffix(self, name: str, suffix_pattern: list) -> list:
        """every manifest entry for one named-file whose file_home's
        TRAILING segments match `suffix_pattern` position-by-position
        (Star3 as wildcard), with any number of additional segments
        (including zero) allowed before them -- the suffix-anchored
        counterpart to _candidates_for_name's exact-length match, used
        by the ':flatten()/...' prefixed shape (any depth, THEN a fixed
        literal/'*'/:name(...) anchor at the end)."""
        manifest = self.source.file_manifest(name)
        home = self.csvpaths.file_manager.named_file_home(name).rstrip("/")
        return [
            entry
            for entry in manifest
            if self._matches_suffix(entry, home, suffix_pattern)
        ]

    def _candidates_for_name_by_prefix_and_suffix(
        self, name: str, prefix_pattern: list, suffix_pattern: list
    ) -> list:
        """every manifest entry for one named-file whose file_home's
        LEADING segments match `prefix_pattern` AND (if non-empty)
        TRAILING segments match `suffix_pattern`, with any number of
        additional segments (including zero) allowed in between -- added
        2026-08-27 for the "literal prefix BEFORE :flatten()" shape
        (e.g. "2025/:flatten()/:name('orders.csv')"). An empty
        `suffix_pattern` still matches -- "prefix, then any depth, no
        further constraint" (a missing suffix, e.g. "2025/:flatten()"
        alone)."""
        manifest = self.source.file_manifest(name)
        home = self.csvpaths.file_manager.named_file_home(name).rstrip("/")
        return [
            entry
            for entry in manifest
            if self._matches_prefix_then_suffix(
                entry, home, prefix_pattern, suffix_pattern
            )
        ]

    def _all_candidates_for_name(self, name: str) -> list:
        """every manifest entry for one named-file, at any path depth --
        ':flatten()'/':groups()' both match unconditionally, unlike a
        pattern (which must match an exact segment count), so this skips
        _matches entirely. Shared by '*' traversal's own is_flattened/
        is_deep_grouped branch (every named-file) and query()'s
        literal-root_major is_flattened/is_deep_grouped branch (this one
        named-file only) -- ':groups()' differs from ':flatten()' only in
        what happens AFTER gathering (partitioned vs. pooled), not in
        which candidates are gathered."""
        manifest = self.source.file_manifest(name)
        home = self.csvpaths.file_manager.named_file_home(name).rstrip("/")
        home_parts = pathu.parts(home)
        return [
            entry
            for entry in manifest
            if pathu.parts(entry["file_home"])[: len(home_parts)] == home_parts
        ]

    @staticmethod
    def _attached_functions_message(*, name_one, star_traversal: bool) -> str:
        """the error for functions attached directly to name_one with no
        separating '.'. When one of them is a field function, e.g.
        ':name("orders.csv"):fingerprint()', the message gives the
        reference with the dot, since name_one picks the file and
        name_three picks the version and reads its fields (E2, option C,
        David 2026-11-02). Otherwise the long-standing message."""
        if name_one is None:
            raise ValueError("name_one cannot be None")
        has_field = False
        for call in name_one.functions:
            function_cls = ReferenceFunctionFactory.get_registered_class(call.name)
            if function_cls is not None and function_cls.SOURCE is not None:
                has_field = True
        if not has_field:
            if star_traversal:
                return (
                    "FilesReferenceFinder3 does not support functions "
                    "attached directly to name_one for '*' traversal -- put "
                    "the version-selecting function in name_three instead."
                )
            return (
                "FilesReferenceFinder3 does not support functions attached "
                "directly to name_one -- put the version-selecting function in "
                "name_three instead."
            )
        path = "/".join(str(segment) for segment in name_one.path)
        functions = "".join(str(call) for call in name_one.functions)
        return (
            "FilesReferenceFinder3 does not support field functions attached "
            "directly to name_one: name_one picks the file, name_three picks "
            "the version and reads its fields. Put them in name_three, after "
            f"a '.': '{path}.{functions}'"
        )

    def _name_one_pointer(self, name_one) -> "FunctionCall3 | None":
        """the version-selecting pointer (:first()/:last()/:index(n))
        when it is the ONLY thing left in `name_one.functions` -- a
        peek, not a pop, deliberately: mirrors _pointer_before_
        manifest()'s own non-mutating design (reference_finder_3.py)
        so both query() and _extract_data() can call this
        independently and get the same answer regardless of which
        runs first/already mutated name_one.path via
        _apply_implied_star() -- popping here (the way
        _extract_gate_field_call() pops its own match) would erase the
        only signal _extract_data() has left to recognize this shape
        once query() is done with it. Added 2026-10-20.

        Closes a real code-vs-spec gap, not a new design: compendium
        5.21's own resolve matrix already documents "name_one, file
        pointer" as legal for FILES ("contents of manifest.json") --
        a lone pointer here implies :manifest(), the same way the
        already-built explicit ':manifest()'+pointer shape
        (_pointer_before_manifest) does. The code never caught up to
        that (David, 2026-10-20: "take the spec over the code"). NOTE:
        the normative examples doc's own "equivalent" ':name(...).
        :last()'/':name(...).:manifest():last()' pairs (e.g. lines
        866/956-957) have a '.' before ':last()' -- confirmed live
        that parses as a real name_three, not a name_one-chained
        function at all, a DIFFERENT (and already correctly working)
        shape; this method and its callers are about the undotted
        form (':name(...):last()', no separating '.'), which the
        grammar parses into name_one.path + name_one.functions.

        Returns None if more than one function is left, the sole one
        is not a pointer, or any OTHER pointer-role function is still
        sitting in name_one.path (e.g. ':index(3):last()' -- a
        malformed/illegal combo the normative doc itself calls out,
        line 284 -- `_apply_implied_star()` only ever relocates the
        LAST path segment, so an earlier pointer wrongly left in
        `.path` would otherwise be silently treated as a harmless,
        no-op path segment instead of the second pointer it actually
        is; caught live by a test before this guard was added). Every
        such case still raises via the caller's own existing
        "functions attached directly to name_one" check, unchanged."""
        if len(name_one.functions) != 1:
            return None
        candidate = name_one.functions[0]
        if not isinstance(candidate, FunctionCall3) or candidate.name not in (
            "first",
            "last",
            "index",
        ):
            return None
        for segment in name_one.path:
            if isinstance(segment, FunctionCall3) and segment.name in (
                "first",
                "last",
                "index",
            ):
                return None
        return candidate

    def _name_one_manifest_call(self, name_one) -> "FunctionCall3 | None":
        """the bare, argument-less ':manifest()' call when it is the
        only thing left in `name_one.functions`, chained (no
        separating '.') directly after a real narrowing prefix in
        `name_one.path` (e.g. ':name("food.csv"):manifest()') -- a
        peek, not a pop, same non-mutating reasoning as
        _pointer_before_manifest() (reference_finder_3.py): so both
        query() and _extract_data() can call this independently and
        get the same answer. Added 2026-10-20 for issue #410.

        The fully-bare ':manifest()' shape (nothing else at all) is
        already intercepted earlier in query() by
        _is_bare_pointer_reference() -- this is specifically the
        combined, name_one-narrowed shape that was missing: maps the
        manifest ENTRY (not a field) over every candidate the
        narrowing prefix matches, the way _bare_manifest_field_call()
        already maps a trailing FIELD over every entry of a fully-bare
        ':manifest()' -- same idea, just with a real narrowing prefix
        instead of none, and no field to drill into."""
        if len(name_one.functions) != 1:
            return None
        candidate = name_one.functions[0]
        if (
            not isinstance(candidate, FunctionCall3)
            or candidate.name != "manifest"
            or candidate.arg is not None
        ):
            return None
        return candidate

    def _extract_gate_field_call(self, name_one) -> "Function3 | None":
        """pops a single GATE-able field-accessor function (e.g.
        ':type("csv")') out of `name_one.functions`, IN PLACE, when it
        is the only thing there and genuinely carries an argument to
        filter by -- leaves `name_one.functions` empty afterward, so
        every bare-shape check below (`_is_bare_all_reference()` etc.)
        sees it exactly as if the field accessor were never there, the
        same "pop it off, handle it separately" pattern
        `ReferenceFinder3._apply_implied_star()` already uses for the
        path itself. Added 2026-10-18 for ':type()'s own GATE
        (compendium 3.9d's own claimed equivalence between the bare and
        explicit-'*' forms, e.g. ":type(\"csv\")" == "*:type(\"csv\")"
        -- both reach this same extraction, just at different points in
        query()'s own dispatch, since the bare form's function still
        sits in `name_one.path` at the point THIS check first runs, not
        `.functions`, until `_apply_implied_star()` moves it there).

        Deliberately narrow, matching exactly what :type()'s own gap
        needs, not a general "any field accessor chains onto name_one"
        capability: excludes SELECTOR_WHEN_ARGUED functions (a
        different, already-decided-against shape -- :uuid()'s own
        bare-selector form has its own, separate dispatch earlier in
        query(), with no pointer/prefix involved at all), any accessor
        with no argument, any accessor not declaring Reference3.
        NAME_ONE legal for FILES in its own POSITIONS (checked the
        same registry-driven way _check_position() does, just
        returning None instead of raising, so the caller's own generic
        "unsupported extra" rejection fires with its existing message)
        -- reading a bare value this way, or chaining a function with
        no NAME_ONE GATE position of its own, is a separate question
        no worked example has asked for yet, left unbuilt rather than
        guessed at (same reasoning `_bare_manifest_field_call()`'s own
        docstring uses elsewhere in this file) -- and, added 2026-10-18
        alongside ':status()'s own build, any accessor with no real
        `KEY` entry for FILES (a genuinely ledger-only field, e.g.
        ':status()' itself, declared via LEDGER_KEY instead -- see
        `username_3.py`'s own established precedent). This candidates
        list is the PER-NAME manifest, which a ledger-only field never
        appears in at all; without this check, a combination no worked
        example asks for (e.g. ':flatten():status("x")') would
        silently match nothing instead of raising, confirmed live
        before adding this guard."""
        if len(name_one.functions) != 1:
            return None
        candidate = name_one.functions[0]
        function_cls = ReferenceFunctionFactory.get_registered_class(candidate.name)
        if (
            function_cls is None
            or function_cls.SOURCE is None
            or function_cls.SELECTOR_WHEN_ARGUED
            or candidate.arg is None
            or function_cls.KEY.get(Reference3.FILES) is None
            or Reference3.NAME_ONE
            not in (function_cls.POSITIONS.get(Reference3.FILES) or ())
        ):
            return None
        field_call = self._build(candidate)
        name_one.functions.pop(0)
        return field_call

    def _bare_status_gate_chain(self, name_one) -> "list | None":
        """returns the full chain of GATE-able field-accessor
        instances (built, real Function3 objects) when name_one's
        entire content is a bare ':status(...)' chain -- ':status()'
        itself as the sole path segment, carrying its own argument,
        with zero or more additional chained field accessors (e.g.
        ':named_file_name("orders")'), each ALSO carrying its own
        argument -- or None if this shape does not apply. Added
        2026-10-18 for the normative doc's own "$*.files.:status(
        \"failed\"):named_file_name(\"orders\")" ("select named-files
        registrations for orders that failed"; the status was
        "Registration failed" until 2026-10-26).

        Named/narrow, matching `_bare_manifest_field_call()`'s own
        established style in this file, rather than the more generic
        `_extract_gate_field_call()` above -- ':status()' is the ONLY
        field that exists SOLELY in the global arrivals ledger
        (confirmed live against the real registration code: never
        written to any per-name manifest, a failed registration often
        has no real name/path to file itself under), so this reads the
        ledger DIRECTLY rather than going through the ordinary PER-
        NAME-manifest candidate pipeline `_extract_gate_field_call()`
        feeds at all -- a genuinely different data source, not just a
        different filter on the same one. Detecting "this bare chain
        needs the ledger" is keyed specifically on seeing ':status()'
        as the chain's own first member, not on a declarative per-
        function flag -- there is currently no second ledger-only
        root trigger to generalize from (contrast `_matches_field_
        predicate()`'s own `KEY` check for ordinary chain MEMBERS,
        which IS generic). UPDATED 2026-11-05: ':lifecycle()' is that
        second ledger-only field, so the trigger is now declarative --
        any argued member with a FILES LEDGER_KEY and no FILES KEY
        (_is_ledger_only_gate()), in any position, since gates commute.

        Every member (the leading ':status()' and any chained field
        accessors) must carry an argument and declare a real
        `KEY`/`LEDGER_KEY` entry for FILES -- that same per-entry
        lookup is what `FilesReferenceFinder3._filter_ledger_by_gate_
        chain()` uses to read each one directly off a raw ledger
        dict."""
        if len(name_one.path) != 1 or not isinstance(name_one.path[0], FunctionCall3):
            return None
        calls = [name_one.path[0], *name_one.functions]
        #
        # 2026-11-05: any argued ledger-only member starts the chain, not
        # just a leading ':status()'. ':lifecycle()' is the second ledger-
        # only field, and gates commute (compendium 6.1), so
        # ':named_file_name("orders"):status("failed")' is the same chain
        # as ':status("failed"):named_file_name("orders")' -- it used to
        # raise.
        #
        if not any(self._is_ledger_only_gate(call) for call in calls):
            return None
        built = []
        for call in calls:
            function_cls = ReferenceFunctionFactory.get_registered_class(call.name)
            key = None
            if function_cls is not None:
                key = function_cls.KEY.get(
                    Reference3.FILES
                ) or function_cls.LEDGER_KEY.get(Reference3.FILES)
            if (
                function_cls is None
                or function_cls.SELECTOR_WHEN_ARGUED
                or call.arg is None
                or key is None
            ):
                return None
            built.append(self._build(call))
        return built

    @staticmethod
    def _is_ledger_only_gate(call: FunctionCall3) -> bool:
        """true for an argued field that only the global arrivals ledger
        holds for FILES and that is legal in name_one there: a LEDGER_KEY,
        no KEY and a NAME_ONE position, e.g. ':status("failed")' and
        ':lifecycle("deleted")'. ':named_file_name()' is ledger-keyed too,
        but name_three-only in FILES, so it rides a chain, never starts one."""
        if call is None:
            raise ValueError("Call cannot be None")
        function_cls = ReferenceFunctionFactory.get_registered_class(call.name)
        if function_cls is None or call.arg is None:
            return False
        return (
            function_cls.KEY.get(Reference3.FILES) is None
            and function_cls.LEDGER_KEY.get(Reference3.FILES) is not None
            and Reference3.NAME_ONE in function_cls.POSITIONS.get(Reference3.FILES, ())
        )

    @staticmethod
    def _filter_ledger_by_gate_chain(ledger: list, chain: list) -> list:
        """every global-ledger entry matching ALL of `chain`'s own
        GATE arguments (AND-combined) -- e.g. ':status("failed"):
        named_file_name("orders")' keeps only entries where
        BOTH match. Added 2026-10-18 alongside `_bare_status_gate_
        chain()`, the only current producer of `chain` -- reads each
        member's own value directly off the raw ledger dict via
        `KEY`/`LEDGER_KEY` (whichever is populated for FILES), the
        same dual lookup `_bare_status_gate_chain()` itself already
        validated is present on every member."""
        results = []
        for entry in ledger:
            matched = True
            for field_call in chain:
                key = field_call.KEY.get(
                    Reference3.FILES
                ) or field_call.LEDGER_KEY.get(Reference3.FILES)
                if not ReferenceFinder3._matches_field_predicate(
                    entry.get(key), field_call.arg
                ):
                    matched = False
                    break
            if matched:
                results.append(entry)
        return results

    def _pointer_into_status_matches(
        self, reference: Reference3, matched: list
    ) -> ReferenceResults3:
        """name_three riding alongside a bare ':status(...)' lookup --
        added 2026-10-20 (not-yet-supported sweep #2), closing the gap
        both `query()` call sites above used to reject outright.
        `matched` is already the status-filtered ledger entries (every
        candidate the bare chain selects); unlike the per-name manifest
        shapes elsewhere in this file, ledger entries are NOT guaranteed
        to also exist in `get_manifest(root_major)` (a failed
        registration is ledger-only, see `file_manager.py`'s own
        `_registration_failed()`), so `_extract_data()`'s ordinary
        METADATA_FIELD-by-uuid re-derivation (which reads
        `get_manifest(root_major)` for a literal root) cannot safely
        back a chained field accessor here. Scoped to exactly one
        version-selecting POINTER (:first()/:last()/:index(n)) and
        nothing else riding alongside it -- a literal body, a field
        accessor, or a range function would all need that same ledger-
        vs-manifest plumbing fixed in `_extract_data()` first, and no
        worked example asks for any of them yet, so they stay a clear
        rejection rather than a guess. A lone pointer needs no such
        fix: it only reduces `matched` to the one entry it selects, and
        the returned result's own path/uuid already point straight at
        that entry (the same plain FIRST_PARTY default every other
        pointer-reduced FILES reference already resolves to -- no
        `_extract_data()` changes needed at all)."""
        name_three = reference.name_three
        if name_three.body is not None:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support a literal "
                "name_three body alongside a bare ':status(...)' lookup "
                "-- name_three must resolve to a single version-selecting "
                "pointer (:first()/:last()/:index(n))."
            )
        built = self._build_chain(name_three.functions)
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        if len(built) != 1 or len(pointers) != 1:
            raise ReferenceException3(
                "FilesReferenceFinder3 only supports a single version-"
                "selecting pointer (:first()/:last()/:index(n)) in "
                "name_three alongside a bare ':status(...)' lookup -- a "
                "field accessor or range function riding alongside it is "
                "not yet supported."
            )
        self._check_position(pointers[0], Reference3.NAME_THREE, Reference3.FILES)
        selected = self._apply_pointer(pointers[0], matched)
        if selected is None:
            return ReferenceResults3(results=[])
        return ReferenceResults3(
            results=[
                ReferenceResult3(
                    path=self._ledger_entry_result_path(selected),
                    uuid=selected.get("uuid"),
                )
            ]
        )

    def _ledger_entry_result_path(self, entry: dict) -> str:
        """the real path to use for a `ReferenceResult3` built from a
        raw global-ledger entry -- added 2026-10-18, caught live before
        shipping: `ReferenceResult3` itself forbids a None/empty path,
        but a "failed" entry's own "file_path" is always
        None (the registration never got that far -- confirmed against
        `file_manager.py`'s own `_registration_failed()`, which never
        sets `file_path`/`file_home`/`file_name` at all). Falls back to
        "origin_path" (the attempted source file -- the one real path
        a failure entry usually carries) when "file_path" is empty.
        Widened 2026-10-21: "origin_path" itself can ALSO be empty --
        confirmed live this is exactly the shape the one real, tested
        trigger for this status produces (add_named_file(path="") --
        see test_file_registration_failed), not a hypothetical. Falls
        back a second time, to the global arrivals ledger's own
        manifest.json -- the one real path that always exists and
        genuinely contains this entry -- so a reference can still
        select and report it instead of raising on the one input
        actually confirmed to cause it. Converted from @staticmethod
        to read self.csvpaths.config for this fallback; every existing
        call site already invokes this as self._ledger_entry_result_
        path(...), so no call site changes."""
        path = entry.get("file_path") or entry.get("origin_path")
        if not path:
            return self._files_ledger_path()
        return path

    def _files_ledger_path(self) -> str:
        """the global arrivals ledger's own manifest.json."""
        return Nos(self.csvpaths.config.inputs_files_path).join("manifest.json")

    def _live_ledger_entries(self, *, names: list) -> list:
        """the files ledger entries of the live versions of `names`, in
        ledger order: an entry whose uuid is in one of those named-files'
        own manifests. A failed registration, or a deleted version, has
        no such entry, and neither does a live version with no ledger
        entry (a manifest from before the ledger). No names, no entries:
        '*' over a files root that has no named-files."""
        if names is None:
            raise ValueError("names cannot be None")
        live = set()
        for name in names:
            live.update(e.get("uuid") for e in self.source.file_manifest(name))
        return [e for e in self.source.files_ledger() if e.get("uuid") in live]

    def _live_manifest_entry_by_uuid(self, uuid: str) -> "dict | None":
        """the entry for `uuid` in whichever live named-file's own
        manifest holds it, or None."""
        return self._live_named_file_entry(uuid)[1]

    def resolve(self) -> ReferenceResults3:
        # query() resets the live index; its resolve reuses it, so one
        # resolve() reads each live manifest at most once (reviewer on
        # #585). The base resolve() would reset it again.
        return super().resolve_from(self.query())

    def resolve_from(self, selection: ReferenceResults3 | list) -> ReferenceResults3:
        # the live entries are read at most once per call (_live_index())
        self._live_entries = None
        return super().resolve_from(selection)

    def _query_status_gate(
        self, *, reference: Reference3, status_chain: list, names: list
    ) -> ReferenceResults3:
        """a bare ':status()' gate chain over the live versions of `names`
        (the ledger entries of live versions, in ledger order; C1
        bare-half revert, 2026-11-01), then a name_three pointer if there
        is one. Shared by '*' and ':regex()'/':choice()'."""
        if status_chain is None:
            raise ValueError("status_chain cannot be None")
        if names is None:
            raise ValueError("names cannot be None")
        ledger = self._live_ledger_entries(names=names)
        matched = self._filter_ledger_by_gate_chain(ledger, status_chain)
        if reference.name_three is not None:
            return self._pointer_into_status_matches(reference, matched)
        return ReferenceResults3(
            results=[
                ReferenceResult3(
                    path=self._ledger_entry_result_path(e),
                    uuid=e.get("uuid"),
                )
                for e in matched
            ]
        )

    def _query_ledger_pointer(
        self, *, pointer_call: FunctionCall3, name_filter: "str | None"
    ) -> ReferenceResults3:
        """Rule 1b: the one record a pointer picks from the ledger set, in
        ledger order, the set filtered by name for ':regex()' or
        ':choice()' (6.13b, 6.13b(ii)). The result is the ledger's path
        with the record's uuid (5.7)."""
        if pointer_call is None:
            raise ValueError("pointer_call cannot be None")
        ledger = [
            e
            for e in self.source.files_ledger()
            if name_filter is None
            or re.search(name_filter, e.get("named_file_name") or "")
        ]
        selected = self._apply_pointer(pointer_call, ledger)
        if selected is None:
            return ReferenceResults3(results=[])
        return ReferenceResults3(
            results=[
                ReferenceResult3(path=self._files_ledger_path(), uuid=selected["uuid"])
            ]
        )

    def _live_index(self) -> dict:
        """uuid -> (named-file name, entry) for every live named-file's
        manifest entries, read once per query(), resolve() or resolve_from()
        call (query() and resolve_from() reset it; resolve() keeps the one
        its query() built). Reads of a ledger set record's live
        entry, in a gate, a date bound or resolve, would otherwise walk
        every manifest once per record: on a cloud backend every read
        costs (reviewer on #585)."""
        index = self._live_entries
        if index is None:
            index = {}
            for name in self.source.file_names():
                for e in self.source.file_manifest(name):
                    index.setdefault(e.get("uuid"), (name, e))
            self._live_entries = index
        return index

    def _with_live_times(self, entries: list) -> list:
        """the ledger set records with each live record's time taken from
        its named-file's own entry, so a date range or time window beside
        ':manifest()' filters on the time ':time()' resolves (decision D7,
        2026-11-12). A ledger-only record keeps its own. Membership and
        order are the ledger's."""
        if entries is None:
            raise ValueError("entries cannot be None")
        timed = []
        for e in entries:
            _, live = self._live_index().get(e.get("uuid"), (None, None))
            time = None if live is None else live.get("time")
            timed.append(e if time is None else {**e, "time": time})
        return timed

    def _live_named_file_entry(self, uuid: str) -> tuple:
        """(name, entry) for the live named-file whose own manifest holds
        `uuid`, or (None, None). The FILES counterpart of CSVPATHS'
        _group_manifest_entry() under a traversal root."""
        if not uuid:
            raise ValueError("uuid cannot be None or empty")
        return self._live_index().get(uuid, (None, None))

    def _root_manifest_path(self, name: str) -> str:
        """the manifest.json of the one named-file a literal root_major
        names. See _named_file_manifest_path() for why a reference that
        names a manifest entry gives this path on query()."""
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string")
        home = self.csvpaths.file_manager.named_file_home(name)
        return Nos(home).join("manifest.json")

    def _named_file_manifest_path(self, *, entry: dict, names: list) -> str:
        """the manifest.json of the named-file that holds `entry`. A
        reference that names a manifest entry (an explicit ':manifest()')
        gives this path on query(), with the entry's own uuid: the file
        the entry is read from (compendium 5.7's pattern, agreed with
        David 2026-11-01). `names` are the named-files the entry can
        belong to: root_major's one name, or every name '*' traversal
        read. The entry's file_home sits under its named-file's home,
        the same placement _matches() relies on."""
        if not isinstance(entry, dict):
            raise TypeError("entry must be a dict")
        if not names:
            raise ValueError("names cannot be None or empty")
        file_home = entry.get("file_home")
        if not file_home:
            raise ValueError(f"manifest entry {entry.get('uuid')!r} has no file_home")
        file_parts = pathu.parts(file_home)
        for name in names:
            home = self.csvpaths.file_manager.named_file_home(name).rstrip("/")
            home_parts = pathu.parts(home)
            if file_parts[: len(home_parts)] == home_parts:
                return Nos(home).join("manifest.json")
        raise ReferenceException3(
            f"FilesReferenceFinder3 found no named-file holding the manifest "
            f"entry {entry.get('uuid')!r} (file_home {file_home!r})."
        )

    @staticmethod
    def _is_bare_all_reference(name_one) -> bool:
        """true when name_one's entire content is a single, argument-
        less ':all()' call, with no trailing function chain -- name_three
        (the per-group reduction function) is independent and may or may
        not be present, unlike _is_bare_pointer_reference's shape."""
        return (
            not name_one.functions
            and len(name_one.path) == 1
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name == "all"
            and name_one.path[0].arg is None
        )

    @staticmethod
    def _is_bare_flatten_reference(name_one) -> bool:
        """same shape as _is_bare_all_reference, for ':flatten()'
        instead of ':all()' -- the two are structurally exclusive (a
        single FunctionCall3 cannot be named both at once), so callers
        never need to guard against both being true together."""
        return (
            not name_one.functions
            and len(name_one.path) == 1
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name == "flatten"
            and name_one.path[0].arg is None
        )

    @staticmethod
    def _is_bare_groups_reference(name_one) -> bool:
        """same shape as _is_bare_all_reference/_is_bare_flatten_
        reference, for ':groups()' -- structurally exclusive with both
        (a single FunctionCall3 cannot be named "all"/"flatten"/"groups"
        at once), so callers never need to guard against more than one
        being true together."""
        return (
            not name_one.functions
            and len(name_one.path) == 1
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name == "groups"
            and name_one.path[0].arg is None
        )

    @staticmethod
    def _is_flatten_prefixed_reference(name_one) -> bool:
        """true when name_one's path STARTS with a bare ':flatten()'
        followed by at least one more segment -- the mirror image of
        _is_bare_flatten_reference (which requires ':flatten()' to be
        the ONLY segment). Does not check the arg here -- query() raises
        its own clear error for that, mirroring how the bare-shape
        checks fold the arg check into the boolean instead (this one
        needs to distinguish "wrong arg" from "not this shape at all"
        for a better error message, so it is checked by the caller)."""
        return (
            len(name_one.path) > 1
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name == "flatten"
        )

    @staticmethod
    def _is_prefixed_flatten_reference(name_one) -> bool:
        """true when name_one's path contains exactly one bare
        ':flatten()' call, NOT as the first segment (that is
        _is_flatten_prefixed_reference's own shape, checked first) --
        added 2026-08-27 for the "literal prefix BEFORE :flatten()"
        shape, e.g. "2025/:flatten()/:name('orders.csv')". A second
        ':flatten()' anywhere in the same path is not this shape (there
        is no established meaning for two 'any depth' markers in one
        pattern) -- correctly falls through to the ordinary
        _compile_path_pattern path instead, which raises its own clear
        "not a legal path segment" error for the second one. Does not
        check the arg here, same reasoning
        _is_flatten_prefixed_reference's own docstring gives -- query()
        raises its own clear error for that once this shape is
        confirmed."""
        flatten_indices = [
            i
            for i, seg in enumerate(name_one.path)
            if isinstance(seg, FunctionCall3) and seg.name == "flatten"
        ]
        return len(flatten_indices) == 1 and flatten_indices[0] > 0

    @staticmethod
    def _bare_manifest_field_call(name_one) -> "FunctionCall3 | None":
        """returns the field-accessor FunctionCall3 chained onto a bare,
        argument-less ':manifest()' occupying name_one's own path (e.g.
        ':manifest():uuid()', ':manifest():time()'), or None if this
        shape does not apply. Added 2026-08-28, David's own worked
        examples ("get uuids from all registrations," "get all acme
        registration uuids") -- maps the given field over EVERY entry in
        the matched manifest (the named-file's own, for a literal root;
        the global arrivals ledger, for '*'), unlike the ordinary field-
        accessor position (riding beside a real pointer in name_three),
        which reads the field off exactly the one entity a pointer
        already picked. David confirmed both remain valid, distinct
        ways to reach the same kind of value (narrow to one version via
        :name(...)+pointer, THEN :uuid() in name_three; or map :uuid()
        over every version at once via this shape) -- this does not
        touch or replace the name_three path at all.

        Requires exactly one chained function -- picking one field per
        entry from more than one chained accessor at once is not a
        shape any worked example has asked for yet, so left unbuilt
        rather than guessed at.

        The chained field must be one read from manifest.json. A
        definition.json field (e.g. ':manifest():on_arrival()') raises
        here: it has nothing to read in a manifest entry, and under '*'
        it used to crash in resolve()."""
        if (
            len(name_one.path) != 1
            or not isinstance(name_one.path[0], FunctionCall3)
            or name_one.path[0].name != "manifest"
            or name_one.path[0].arg is not None
        ):
            return None
        if len(name_one.functions) != 1:
            return None
        call = name_one.functions[0]
        if not isinstance(call, FunctionCall3):
            return None
        function_cls = ReferenceFunctionFactory.get_registered_class(call.name)
        if function_cls is None or function_cls.SOURCE is None:
            return None
        if function_cls.SOURCE == "definition":
            raise ReferenceException3(
                f"':{call.name}()' reads definition.json, not manifest.json, "
                "so it is not supported on ':manifest()' -- use "
                f"':{call.name}()' on its own."
            )
        return call

    @staticmethod
    def _manifest_chain(*, name_one) -> "dict | None":
        """the parts of a general chain on a bare ':manifest()' in
        name_one, e.g. ':manifest():last():uuid()' or
        ':manifest():status("failed"):named_file_name("orders")' (finding
        E, 2026-11-02): {"pointer": the one pointer or None, "ranges": the
        range bounds and bare time windows, "gates": the argued fields,
        "values": the unargued fields}. The functions are ANDed in any
        order (compendium 6.1).

        Returns None for any other shape, including the two-function
        shapes that have their own branches: ':manifest():<field>()'
        (_bare_manifest_field_call) and a pointer with ':manifest()' in
        either order (_pointer_before_manifest). A lone range or window
        beside ':manifest()' is claimed here, e.g. ':manifest():yesterday()'
        (2026-11-07; it used to be taken for a field). Only pointers,
        ranges and field functions are claimed; a chain with anything
        else, e.g. ':name()', keeps its old handling. A field that does
        not read manifest.json raises."""
        if name_one is None:
            raise ValueError("name_one cannot be None")
        if len(name_one.path) != 1:
            return None
        calls = [name_one.path[0], *name_one.functions]
        if not all(isinstance(c, FunctionCall3) for c in calls):
            return None
        manifests = [c for c in calls if c.name == "manifest" and c.arg is None]
        if len(manifests) != 1:
            return None
        others = [c for c in calls if c is not manifests[0]]
        if not others:
            return None
        pointer_names = ("first", "last", "index")
        range_names = ("from", "to", "before", "after")

        def _is_range(call) -> bool:
            # a range bound or a bare time window (compendium 6.27e),
            # as CSVPATHS and RESULTS take beside ':manifest()'
            if call.name in range_names:
                return True
            function_cls = ReferenceFunctionFactory.get_registered_class(call.name)
            return function_cls is not None and issubclass(
                function_cls, TimeWindowFunction3
            )

        if (
            len(others) == 1
            and not _is_range(others[0])
            and (calls[0] is manifests[0] or others[0].name in pointer_names)
        ):
            return None
        pointers = []
        ranges = []
        fields = []
        for call in others:
            if call.name in pointer_names:
                pointers.append(call)
                continue
            if _is_range(call):
                ranges.append(call)
                continue
            function_cls = ReferenceFunctionFactory.get_registered_class(call.name)
            if function_cls is None or function_cls.SOURCE not in (
                "manifest",
                "definition",
                "computed",
            ):
                return None
            fields.append((call, function_cls))
        if len(pointers) > 1:
            raise ReferenceException3(
                "A ':manifest()' chain can have at most one pointer "
                "(:first()/:last()/:index(n)), not "
                + ", ".join(f":{p.name}()" for p in pointers)
                + "."
            )
        for call, function_cls in fields:
            if (
                function_cls.SOURCE != "manifest"
                or Reference3.FILES not in function_cls.DATATYPES
            ):
                raise ReferenceException3(
                    f"':{call.name}()' does not read a named-file's "
                    "manifest.json, so it is not supported in a "
                    "':manifest()' chain."
                )
        return {
            "pointer": pointers[0] if pointers else None,
            "ranges": ranges,
            "gates": [call for call, _ in fields if call.arg is not None],
            "values": [call for call, _ in fields if call.arg is None],
        }

    def _query_manifest_chain(
        self, *, reference: Reference3, chain: dict, name_filter: "str | None"
    ) -> ReferenceResults3:
        """query() for a general ':manifest()' chain (_manifest_chain()).
        The pool is the named-file's own manifest for a literal root, and
        the ledger set for '*', ':regex()' or ':choice()', failures
        included. Every gate filters first, then the pointer picks, so
        the written order does not matter. Each result is the entry's
        uuid with the manifest.json that holds it (compendium 5.7)."""
        if chain is None:
            raise ValueError("chain cannot be None")
        if reference.name_three is not None:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not support combining a "
                "':manifest()' chain with name_three -- put the pointer in "
                "the chain instead (e.g. ':manifest():last():uuid()')."
            )
        root_major = reference.root_major
        if isinstance(root_major, str):
            entries = self.source.file_manifest(root_major)
            path = self._root_manifest_path(root_major)
        else:
            entries = [
                e
                for e in self.source.files_ledger()
                if name_filter is None
                or re.search(name_filter, e.get("named_file_name") or "")
            ]
            path = self._files_ledger_path()
        # a live record's time is its live entry's, when a range will read
        # it (decision D7)
        if not isinstance(root_major, str) and chain["ranges"]:
            entries = self._with_live_times(entries)
        # the range first, then the gates, then the pointer (6.28)
        entries = self._apply_manifest_chain_ranges(
            ranges=chain["ranges"], entries=entries
        )
        for gate in chain["gates"]:
            entries = self._filter_by_manifest_chain_gate(
                reference=reference, call=gate, entries=entries
            )
        if chain["pointer"] is not None:
            selected = self._apply_pointer(chain["pointer"], entries)
            entries = [] if selected is None else [selected]
        values = chain["values"]
        if len(values) > 1:
            self.csvpaths.logger.warning(
                "Reference resolves to the value of the last field-accessor "
                "function in its chain (:%s()) -- :%s() earlier in the same "
                "chain could also have provided a value; see compendium 5.20b.",
                values[-1].name,
                "(), :".join(f.name for f in values[:-1]),
            )
        # several whole entries of one named-file cannot be resolved at
        # once (Rule 1, 2026-11-08); a field can (Rule 3), and so can the
        # ledger under '*', ':regex()' or ':choice()' (Rule 1a)
        return ReferenceResults3(
            results=[ReferenceResult3(path=path, uuid=e["uuid"]) for e in entries],
            ambiguous_content_read=(
                isinstance(root_major, str) and not values and len(entries) > 1
            ),
        )

    def _apply_manifest_chain_ranges(self, *, ranges: list, entries: list) -> list:
        """the entries a ':manifest()' chain's range or bare time window
        keeps (2026-11-07), as CSVPATHS and RESULTS narrow beside
        ':manifest()'. A window or a date bound matches each entry's own
        time; an index bound slices the entries in their manifest order,
        the ledger's order under '*'. With no range, every entry."""
        if ranges is None:
            raise ValueError("ranges cannot be None")
        if entries is None:
            raise ValueError("entries cannot be None")
        if not ranges:
            return entries
        built = self._build_chain(ranges)
        windows = [f for f in built if isinstance(f, TimeWindowFunction3)]
        lower_call, upper_call = self._range_calls_from_built(built)
        has_range = lower_call is not None or upper_call is not None
        if len(windows) > 1:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not support combining more "
                "than one bare time-component function (e.g. "
                "':yesterday()') in the same ':manifest()' chain."
            )
        if windows and has_range:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not support combining a bare "
                "time-component function (e.g. ':yesterday()') with an "
                "explicit ':from()'/':to()'/':before()'/':after()' bound "
                "in the same ':manifest()' chain -- the bare function "
                "already means its own whole period, both ends included."
            )
        if windows:
            return self._apply_bare_time_window_to_manifest(entries, windows[0])
        bounds = [
            self._range_bound(c) for c in (lower_call, upper_call) if c is not None
        ]
        for bound in bounds:
            if isinstance(bound, str):
                self._validate_date_format(bound)
        # index and date bounds may mix (6.32)
        return self._apply_mixed_range(
            entries=entries,
            lower_call=lower_call,
            upper_call=upper_call,
            date_filter=self._apply_manifest_date_range,
        )

    def _manifest_chain_field_value(
        self, *, reference: Reference3, function_cls: type, entry: dict | None
    ) -> object:
        """the value of a ':manifest():<field>()' field on one manifest
        entry: a ledger entry under '*', the named-file's own manifest
        entry for a literal root. Shared by resolve() and by the gate in
        query(), so a gate always matches on the value resolve() would
        show."""
        if function_cls.NAME == "named_file_name" and isinstance(
            reference.root_major, str
        ):
            # at FILES scope the name is the literal root itself. under
            # '*', ':regex()' or ':choice()' it is read from each entry.
            return reference.root_major
        key_path = function_cls.KEY.get(Reference3.FILES)
        if self._is_traversal_root(reference.root_major) and entry is not None:
            #
            # a ledger set record: the set decides membership and order,
            # but a live record's details come from its named-file's own
            # entry, the ledger's only where that has none (lifecycle,
            # status, the name). 6.13b(v); C1, as CSVPATHS reads it;
            # decision D7, 2026-11-12. The ledger record alone until then,
            # so '$*' and '$alpha' could disagree. A gate reads through
            # here too, so it matches on the value resolve() shows.
            #
            live = self._live_manifest_entry_by_uuid(entry["uuid"])
            value = self._extract_field_value(live, key_path)
            if value is not None:
                return value
        return self._extract_field_value_with_ledger_fallback(
            entry=entry,
            key_path=key_path,
            function_cls=function_cls,
            datatype=Reference3.FILES,
            ledger_entry_getter=lambda: self._find_manifest_entry_by_uuid(
                self.source.files_ledger(), None if entry is None else entry["uuid"]
            ),
        )

    def _filter_by_manifest_chain_gate(
        self, *, reference: Reference3, call: FunctionCall3, entries: list
    ) -> list:
        """the entries whose field matches `call`'s argument, for a
        ':manifest():<field>(arg)' gate, e.g. ':manifest():status("failed")'.
        Without an argument, every entry. The argument is built first, so
        a field that does not take one raises instead of being silently
        ignored, which is what used to happen here."""
        if call.arg is None:
            return entries
        function_cls = ReferenceFunctionFactory.get_registered_class(call.name)
        if function_cls.SOURCE != "manifest":
            raise ReferenceException3(
                f"':{call.name}()' cannot filter a manifest -- only a "
                "manifest.json field can be used as a gate on ':manifest()'."
            )
        built = self._build(call)
        return [
            e
            for e in entries
            if self._matches_field_predicate(
                self._manifest_chain_field_value(
                    reference=reference, function_cls=function_cls, entry=e
                ),
                built.arg,
            )
        ]

    @staticmethod
    def _is_name_three_gate(function) -> bool:
        """true when `function` is a field with an argument that filters
        the versions it rides with in name_three, e.g. ':type("csv")'
        in '.:last():type("csv")' (finding G, 2026-11-02). Only a
        manifest.json field with a FILES key can filter. A definition.json
        field is not a gate; some of those use the argument to pick a key
        (':source_port("email")'). Argued ':uuid()'/':fingerprint()' are
        gates too (2026-11-06, compendium 6.44)."""
        if function is None:
            raise ValueError("function cannot be None")
        if function.arg is None or isinstance(function, TimeWindowFunction3):
            return False
        function_cls = ReferenceFunctionFactory.get_registered_class(function.name)
        if function_cls is None or function_cls.SOURCE != "manifest":
            return False
        if Reference3.FILES not in function_cls.DATATYPES:
            return False
        key = function_cls.KEY.get(Reference3.FILES) or function_cls.LEDGER_KEY.get(
            Reference3.FILES
        )
        return key is not None

    def _filter_by_gates(
        self, *, reference: Reference3, gates: list, candidates: list
    ) -> list:
        """the candidates matching every gate (AND), each field read the
        way resolve() reads it, so ':status()' works through the ledger
        fallback. `gates` are built functions (_is_name_three_gate())."""
        if gates is None:
            raise ValueError("gates cannot be None")
        if candidates is None:
            raise ValueError("candidates cannot be None")
        for gate in gates:
            function_cls = ReferenceFunctionFactory.get_registered_class(gate.name)
            candidates = [
                c
                for c in candidates
                if self._matches_field_predicate(
                    self._manifest_chain_field_value(
                        reference=reference, function_cls=function_cls, entry=c
                    ),
                    gate.arg,
                )
            ]
        return candidates

    def _extract_data(self, result: ReferenceResult3):
        reference = self.ref.parsed
        log_call = self._bare_log_call(reference)
        if log_call is not None:
            return self._read_log_file(result.path, log_call.arg)
        manifest_chain = None
        definition_calls = None
        if reference.name_three is None:
            manifest_chain = self._manifest_chain(name_one=reference.name_one)
            definition_calls = self._definition_chain(name_one=reference.name_one)
        if definition_calls is not None:
            return self._definition_chain_data(
                reference=reference, calls=definition_calls, path=result.path
            )
        if manifest_chain is not None:
            # a general ':manifest()' chain (finding E): the entry query()
            # matched, or the last unargued field's value on it. a gate
            # only filters, it supplies no value (finding D).
            if isinstance(reference.root_major, str):
                entries = self.source.file_manifest(reference.root_major)
            else:
                entries = self.source.files_ledger()
            entry = self._find_manifest_entry_by_uuid(entries, result.uuid)
            values = manifest_chain["values"]
            if not values:
                # a live record of the ledger set is its live entry, as
                # for Rule 1b (D6) and the bare filter-only read (D7)
                if not isinstance(reference.root_major, str):
                    live = self._live_manifest_entry_by_uuid(result.uuid)
                    if live is not None:
                        return live
                return entry
            return self._manifest_chain_field_value(
                reference=reference,
                function_cls=ReferenceFunctionFactory.get_registered_class(
                    values[-1].name
                ),
                entry=entry,
            )
        if (
            reference.name_three is None
            and result.uuid is not None
            and self._name_one_pointer(reference.name_one) is not None
            # ':manifest():last()' is Rule 1b, as ':last():manifest()' is:
            # under '*' a record of the ledger set, resolved below. This
            # branch read the live entry for it and gave None for a
            # ledger-only record (2026-11-12).
            and self._pointer_before_manifest(reference, "manifest") is None
        ):
            # compendium 5.21's "name_one, file pointer" shape -- a lone
            # pointer (:first()/:last()/:index(n)) directly in name_one
            # implies :manifest(), same as the explicit ':manifest()'+
            # pointer shape just below (_pointer_before_manifest)
            # already means. Checked here, BEFORE resolve_kind is read:
            # resolve_kind's own generic classification has nothing to
            # go on here (the pointer itself carries no
            # metadata_kind() of its own, unlike an explicit
            # ':manifest()' call), so it would otherwise default to
            # FIRST_PARTY and never reach the re-derive-by-uuid logic
            # the kind == METADATA_FILE block below uses for every
            # other shape that selects one manifest entry this way.
            if self._is_traversal_root(reference.root_major):
                # each named-file's own pick (4.1b), in its own manifest.
                # ':regex()' and ':choice()' are a filtered '*' (6.13b(iv));
                # they were Star3 only until 2026-11-12 and passed their
                # FunctionCall3 to file_manifest().
                return self._live_manifest_entry_by_uuid(result.uuid)
            manifest = self.source.file_manifest(reference.root_major)
            return self._find_manifest_entry_by_uuid(manifest, result.uuid)
        kind = reference.resolve_kind
        if kind == Reference3.METADATA_FIELD and reference.name_three is not None:
            #
            # when every field in name_three is a gate, nothing supplies a
            # value (finding D), so the reference resolves as it would
            # without them: the version's bytes, or its manifest entry
            # beside ':manifest()' (finding G, 2026-11-02).
            #
            built = self._build_chain(reference.name_three.functions)
            fields = [f for f in built if self._find_field_function_call([f])]
            if fields and all(self._is_name_three_gate(f) for f in fields):
                kind = (
                    Reference3.METADATA_FILE
                    if any(f.name == "manifest" for f in built)
                    else Reference3.FIRST_PARTY
                )
        if kind == Reference3.FIRST_PARTY:
            if reference.name_three is None:
                # name_one-terminal (prefix search) result: result.path
                # is a file-home directory, not a version file -- no
                # single unambiguous payload to return, per "creating
                # references v3.txt"'s "Resolve terminating at
                # name_one, with no pointer: no default" rule.
                return None
            worksheet = reference.name_one.name_two
            if worksheet is not None:
                # '#worksheet' marker (settled 2026-08-26, see the
                # "#name_two" bucket-list entry) -- XLSX only, enforced
                # structurally by query() (a pointer is required
                # alongside it, so result.path is always exactly one
                # version file here). XlsxDataReader is row-oriented
                # (.next(), a generator of str lists), not the raw-bytes
                # ".source.read()" every other FIRST_PARTY read uses --
                # DataFileReader itself already understands the
                # "path#sheet" convention (see file_readers.py's own
                # __new__), so the sheet just needs appending to the
                # path, same as any other caller of that convention.
                if not XlsxReaderHelper.is_xlsx(result.path):
                    raise ReferenceException3(
                        f"FilesReferenceFinder3 cannot apply the "
                        f"'#worksheet' marker to {result.path!r} -- it is "
                        "not an XLSX file."
                    )
                with DataFileReader(
                    path=f"{result.path}#{worksheet}", mode="rb"
                ) as reader:
                    return list(reader.next())
            with DataFileReader(path=result.path, mode="rb") as reader:
                return reader.source.read()
        if kind == Reference3.METADATA_FILE:
            if (
                self._is_bare_pointer_reference(reference, "manifest")
                or self._is_bare_pointer_reference(reference, "definition")
                or self._is_bare_pointer_reference(reference, "readme")
            ):
                # result.path is already the manifest.json/definition.json/
                # README.md path itself (set by query()'s
                # _query_well_known_file() branch above). Also covers bare
                # ':definition()' during '*' traversal -- _is_bare_pointer_
                # reference does not look at root_major, and
                # _query_star_traversal's own early METADATA_FILE branch
                # sets result.path the same way for that shape (added
                # 2026-08-27). ':readme()' added 2026-09-21 -- not wired
                # into '*' traversal (no worked example demonstrates or
                # requires it there; see the bucket list).
                return self._read_well_known_file(result.path)
            if (
                isinstance(reference.root_major, str)
                and reference.name_three is None
                and self._name_one_manifest_call(reference.name_one) is not None
                and result.uuid is not None
            ):
                # issue #410 -- query()'s own new branch already
                # produced one ReferenceResult3 per candidate a real
                # name_one narrowing prefix (e.g. ':name("food.csv")')
                # matched; re-derive each one's own manifest entry by
                # uuid, same pattern as every other METADATA_FILE
                # branch here.
                manifest = self.source.file_manifest(
                    reference.root_major
                )
                return self._find_manifest_entry_by_uuid(manifest, result.uuid)
            if (
                self._is_traversal_root(reference.root_major)
                and result.uuid is not None
                and self._pointer_before_manifest(reference, "manifest") is not None
            ):
                # ':regex()'/':choice()' too since 2026-11-12.
                # Rule 1b -- a pointer already reduced the global ledger
                # to one entry in query(). A live record reads its
                # named-file's own entry first, a ledger-only one (a failed
                # arrival, a deleted named-file) its ledger record, as
                # CSVPATHS does under C1 (6.13b(v): the named-entity
                # manifest wins for details; decision D6, 2026-11-12). It
                # read the ledger record alone until then.
                entry = self._live_manifest_entry_by_uuid(result.uuid)
                if entry is not None:
                    return entry
                ledger = self.source.files_ledger()
                return self._find_manifest_entry_by_uuid(ledger, result.uuid)
            if (
                self._is_traversal_root(reference.root_major)
                and result.uuid is not None
                and reference.name_three is not None
            ):
                # '*' traversal selected a live version from one
                # named-file (6.13b(iv)); its entry is in that
                # named-file's own manifest, the path query() gave. Was
                # read from the ledger before 2026-11-01. ':regex()' and
                # ':choice()' too since 2026-11-12 (Star3 only before).
                return self._live_manifest_entry_by_uuid(result.uuid)
            if (
                isinstance(reference.root_major, str)
                and self._pointer_before_manifest(reference, "manifest") is not None
                and result.uuid is not None
            ):
                # symmetry fix, added 2026-10-16 -- the literal-root_major
                # counterpart to Rule 1b just above: query()'s own new
                # branch already ordinal-selected one entry out of THIS
                # named-file's own manifest.json; re-derive it here by
                # uuid, same pattern as every other METADATA_FILE branch
                # in this method.
                manifest = self.source.file_manifest(
                    reference.root_major
                )
                return self._find_manifest_entry_by_uuid(manifest, result.uuid)
            if reference.name_three is not None and any(
                f.contains_function_named("manifest")
                for f in reference.name_three.functions
            ):
                # :manifest() riding alongside a real path/version match
                # (a pointer, or none at all -- see query()) -- give the
                # matched entry itself, not the whole raw file.
                manifest = self.source.file_manifest(
                    reference.root_major
                )
                return self._find_manifest_entry_by_uuid(manifest, result.uuid)
        if kind == Reference3.METADATA_FIELD:
            is_bare_field_call = reference.name_three is None
            #
            # true for ':manifest():<field>()'. such a field is read from
            # the manifest entry, even one like ':template()' that reads
            # definition.json when it stands alone.
            #
            is_manifest_chain = False
            if not is_bare_field_call:
                #
                # the last field that is not a gate supplies the value,
                # with a warning when there are two (compendium 5.20b). it
                # was the first field, a gate included, until 2026-11-02.
                #
                field_call = self._last_field_function_call(
                    [
                        f
                        for f in self._build_chain(reference.name_three.functions)
                        if not self._is_name_three_gate(f)
                    ]
                )
            else:
                # ':manifest():uuid()'-style, chained onto a bare
                # ':manifest()' in name_one -- added 2026-08-28, see
                # query()'s/_query_star_traversal()'s own comment on this
                # shape. result.uuid is real here (query() built it from
                # the actual matched manifest entry), so the ordinary
                # manifest-entry-by-uuid read below applies unchanged --
                # only the "which manifest to search" step (just below)
                # needs to know about '*' root. A bare definition field
                # (':on_arrival()', ':template()') never reaches here: it
                # is a ':definition()' chain, resolved at the top of this
                # method (2026-11-03).
                field_call = self._bare_manifest_field_call(reference.name_one)
                is_manifest_chain = field_call is not None
            if field_call is not None:
                function_cls = ReferenceFunctionFactory.get_registered_class(
                    field_call.name
                )
                if is_manifest_chain and function_cls.SOURCE == "manifest":
                    # the ledger for '*', ':regex()' and ':choice()', as
                    # in _query_manifest_chain(). Was Star3 only, so a
                    # ':regex()' root passed its FunctionCall3 to
                    # file_manifest() and raised TypeError (2026-11-12).
                    if isinstance(reference.root_major, str):
                        manifest = self.source.file_manifest(reference.root_major)
                    else:
                        manifest = self.source.files_ledger()
                    entry = self._find_manifest_entry_by_uuid(manifest, result.uuid)
                    if field_call.arg is not None:
                        #
                        # a field with an argument is a filter. it was
                        # applied in query() and supplies no value, so
                        # the result is the matching manifest entry itself
                        # (compendium 5.21, name_one with a file pointer).
                        # a live record of the ledger set is its live entry,
                        # as for Rule 1b (decision D6).
                        #
                        if not isinstance(reference.root_major, str):
                            live = self._live_manifest_entry_by_uuid(result.uuid)
                            if live is not None:
                                return live
                        return entry
                    return self._manifest_chain_field_value(
                        reference=reference, function_cls=function_cls, entry=entry
                    )
                if function_cls.SOURCE == "computed":
                    # never stored -- comes straight from the already-
                    # resolved reference, no manifest/definition read at
                    # all. see function_3.py's SOURCE comment.
                    return self._compute_field(
                        name=field_call.name, reference=reference, result=result
                    )
                if field_call.name == "named_file_name" and not (
                    self._is_traversal_root(reference.root_major)
                ):
                    # a real, stored field at RESULTS/RESULT scope, but at
                    # FILES scope this is just the already-known resolved
                    # name -- reading it back from the manifest would be
                    # redundant, so it is computed here instead, same
                    # reasoning as the "computed" SOURCE branch above.
                    # under '*' root_major is the '*' itself, not a name,
                    # so the name is read from each ledger entry below.
                    return reference.root_major
                if (
                    field_call.name == "named_file_name"
                    and reference.name_three is not None
                ):
                    # a version a traversal selected: the name of the live
                    # named-file that holds it, as the literal root gives
                    # (6.13b(iv)). The ledger, below, could lack it
                    # (decision D4, 2026-11-12).
                    name, _ = self._live_named_file_entry(result.uuid)
                    if name is not None:
                        return name
                key_path = function_cls.KEY.get(reference.datatype)
                key_path = self._apply_key_arg(key_path, field_call.arg)
                if function_cls.SOURCE == "definition":
                    config = self.csvpaths.file_manager.describer.get_config(
                        self._holding_named_file_name(
                            reference=reference, result=result
                        )
                    )
                    entry = config.model_dump(exclude_none=True)
                    return self._extract_field_value(entry, key_path)
                if self._is_traversal_root(reference.root_major):
                    # root_major is '*', ':regex()' or ':choice()' here, not
                    # a name, so file_manifest() cannot be called with it
                    # (added 2026-08-28 for '*'; ':regex()'/':choice()'
                    # 2026-11-12, which passed their FunctionCall3 to it).
                    #
                    # a name_three field reads the version a traversal
                    # selected the way the literal reference does: its
                    # live named-file's own manifest first, the ledger as
                    # fallback, so ':lifecycle()' (LEDGER_KEY only) still
                    # reads the ledger (6.13b(iv), (v); decision D4,
                    # 2026-11-12). It read the ledger first until then, so
                    # '$*' and '$alpha' could disagree. No supported shape
                    # reaches here without name_three: a bare
                    # ':manifest():<field>()' takes the is_manifest_chain
                    # branch above, and query() rejects any other name_one
                    # field. If one ever does, it must read the ledger
                    # (ruling C Q1, 2026-10-30), so fail loudly rather than
                    # guess.
                    #
                    if reference.name_three is None:
                        raise ReferenceException3(
                            "FilesReferenceFinder3 reached a name_one field "
                            "read under a traversal root, which no supported "
                            "shape does -- it should read the ledger (ruling "
                            "C Q1)."
                        )
                    entry = self._live_manifest_entry_by_uuid(result.uuid)
                else:
                    manifest = self.source.file_manifest(
                        reference.root_major
                    )
                    entry = self._find_manifest_entry_by_uuid(manifest, result.uuid)
                return self._extract_field_value_with_ledger_fallback(
                    entry=entry,
                    key_path=key_path,
                    function_cls=function_cls,
                    datatype=reference.datatype,
                    ledger_entry_getter=lambda: self._find_manifest_entry_by_uuid(
                        self.source.files_ledger(), result.uuid
                    ),
                )
        # confirmed unreachable via any real reference (not-yet-
        # supported sweep #10), not a pending gap: every function that
        # can reach resolve_kind's own METADATA_FILE/METADATA_FIELD
        # classification is already dispatched to its own branch above
        # (bare :manifest()/:definition()/:readme(), the Star3 ledger
        # case, a name_one-narrowed manifest read, every registered
        # field-accessor via field_call) -- TestExtractData's own two
        # tests only reach this line by calling _extract_data()
        # directly with a hypothetical, unregistered function name
        # (":meta()"), something query()/resolve() would already have
        # rejected earlier in build_chain() for any real reference.
        raise ReferenceException3(
            f"FilesReferenceFinder3 does not support resolve_kind={kind!r} "
            "-- only :manifest()/:definition() and registered field-accessor "
            "functions are wired up as metadata-file/field functions."
        )

    def _compute_field(
        self, *, name: str, reference: "Reference3", result: ReferenceResult3
    ) -> object:
        """values for SOURCE == "computed" field-accessor functions --
        never read from a manifest/definition, always derived from the
        already-resolved reference. See function_3.py's SOURCE comment
        and named_file_home_3.py."""
        if name is None or name == "":
            raise ValueError("name cannot be None or empty")
        if name == "named_file_home":
            return self.csvpaths.file_manager.named_file_home(
                self._holding_named_file_name(reference=reference, result=result)
            )
        raise ReferenceException3(
            f"FilesReferenceFinder3 has no computed-field handling for :{name}()"
        )

    def _holding_named_file_name(
        self, *, reference: "Reference3", result: ReferenceResult3
    ) -> str:
        """the name of the named-file a result belongs to: the root for a
        literal root_major; under '*', ':regex()' or ':choice()' the live
        named-file whose own manifest holds the result's version
        (6.13b(iv): the literal reference for each live name). It was
        root_major itself, which is not a name there: ':named_file_home()'
        and a definition field raised or read the wrong named-file
        (2026-11-12). Raises when no live named-file holds the version."""
        if reference is None:
            raise ValueError("reference cannot be None")
        if isinstance(reference.root_major, str):
            return reference.root_major
        if result is None or not result.uuid:
            raise ReferenceException3(
                "FilesReferenceFinder3 cannot tell which named-file a result "
                "belongs to without its version uuid."
            )
        name, _ = self._live_named_file_entry(result.uuid)
        if name is None:
            raise ReferenceException3(
                f"FilesReferenceFinder3 found no live named-file holding "
                f"version {result.uuid!r}."
            )
        return name

    @staticmethod
    def _matches(entry: dict, home: str, pattern: list) -> bool:
        home_parts = pathu.parts(home)
        file_parts = pathu.parts(entry["file_home"])
        if file_parts[: len(home_parts)] != home_parts:
            return False
        segments = file_parts[len(home_parts) :]
        if len(segments) != len(pattern):
            return False
        for actual, expected in zip(segments, pattern):
            if not ReferenceFinder3._segment_matches(expected, actual):
                return False
        return True

    @staticmethod
    def _matches_suffix(entry: dict, home: str, pattern: list) -> bool:
        """like _matches, but matches when file_home's own relative
        segments END WITH `pattern` position-by-position (Star3 as
        wildcard), with any number of additional segments (including
        zero) allowed BEFORE them -- the ':flatten()/...' prefixed
        shape's own matcher: any depth, then a fixed literal/'*'/
        :name(...) anchor at the end. `pattern` is never empty here (the
        caller only reaches this with at least one segment after the
        leading ':flatten()')."""
        home_parts = pathu.parts(home)
        file_parts = pathu.parts(entry["file_home"])
        if file_parts[: len(home_parts)] != home_parts:
            return False
        segments = file_parts[len(home_parts) :]
        if len(segments) < len(pattern):
            return False
        trailing = segments[len(segments) - len(pattern) :]
        for actual, expected in zip(trailing, pattern):
            if not ReferenceFinder3._segment_matches(expected, actual):
                return False
        return True

    @staticmethod
    def _matches_prefix_then_suffix(
        entry: dict, home: str, prefix_pattern: list, suffix_pattern: list
    ) -> bool:
        """like _matches_suffix, but ALSO requires file_home's own
        relative segments to START WITH `prefix_pattern` -- the "literal
        prefix BEFORE :flatten()" shape's own matcher (added
        2026-08-27): a fixed prefix, then any depth, then an OPTIONAL
        fixed suffix at the end. `suffix_pattern` may be empty (a
        missing suffix, e.g. "2025/:flatten()" alone) -- in that case
        only the prefix is checked, "any depth after it" with no further
        constraint."""
        home_parts = pathu.parts(home)
        file_parts = pathu.parts(entry["file_home"])
        if file_parts[: len(home_parts)] != home_parts:
            return False
        segments = file_parts[len(home_parts) :]
        if len(segments) < len(prefix_pattern) + len(suffix_pattern):
            return False
        leading = segments[: len(prefix_pattern)]
        for actual, expected in zip(leading, prefix_pattern):
            if not ReferenceFinder3._segment_matches(expected, actual):
                return False
        if suffix_pattern:
            trailing = segments[len(segments) - len(suffix_pattern) :]
            for actual, expected in zip(trailing, suffix_pattern):
                if not ReferenceFinder3._segment_matches(expected, actual):
                    return False
        return True
