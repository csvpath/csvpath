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
    #    name_one is not yet supported.
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

    def query(self) -> ReferenceResults3:
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
                # root case above -- every ledger entry is a candidate.
                if reference.name_three is not None:
                    raise ReferenceException3(
                        "FilesReferenceFinder3 does not yet support "
                        "combining a bare ':status(...)' lookup with "
                        "name_three -- it reads the global arrivals "
                        "ledger directly, which has no per-name-file "
                        "structure to narrow further."
                    )
                ledger = self.csvpaths.file_manager.files_root_manifest
                matched = self._filter_ledger_by_gate_chain(ledger, status_chain)
                return ReferenceResults3(
                    results=[
                        ReferenceResult3(
                            path=self._ledger_entry_result_path(e),
                            uuid=e.get("uuid"),
                        )
                        for e in matched
                    ]
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
                home = self.csvpaths.config.inputs_files_path
                path = Nos(home).join("manifest.json")
                ledger = self.csvpaths.file_manager.files_root_manifest
                selected = self._apply_pointer(pointer_call, ledger)
                if selected is None:
                    return ReferenceResults3(results=[])
                return ReferenceResults3(
                    results=[ReferenceResult3(path=path, uuid=selected["uuid"])]
                )
            return self._query_star_traversal(reference)

        if isinstance(root_major, FunctionCall3):
            # :regex() at root_major -- added 2026-08-27. Structurally
            # identical to the Star3 case just above (every named-file
            # is a candidate), just pre-filtered by pattern before
            # _query_star_traversal() enumerates -- see its own
            # name_filter docstring. No other function is legal here;
            # the grammar itself is permissive (any function, see
            # reference_grammar_3.py's own note) so this is a semantic
            # check, not a grammar-level one.
            if root_major.name != "regex":
                raise ReferenceException3(
                    f":{root_major.name}() is not a legal root_major "
                    "function -- only :regex() is supported."
                )
            built = self._build(root_major)
            return self._query_star_traversal(reference, name_filter=built.pattern)

        name_one = reference.name_one
        if (
            name_one.name_two is not None
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name not in ("name", "regex")
        ):
            # '#worksheet' only means anything against a literal named-
            # file path (there is one specific file to have worksheets
            # in) -- ':name("...")'/':regex(...)' are both path-BUILDING
            # (a literal name, or a pattern match, added 2026-09-23 for
            # ':regex()' -- same reasoning), same as any other literal
            # path segment, so both are exempt here same as they are
            # from _is_bare_function_only's own "bare marker" test; a
            # bare context-setter/pointer/marker function occupying
            # name_one's entire content (':manifest()', ':all()',
            # ':home()', etc.) has no file of its own to read a
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
            # real a need as the '*' form below, built together.
            if reference.name_three is not None:
                raise ReferenceException3(
                    "FilesReferenceFinder3 does not yet support combining "
                    "a bare ':status(...)' lookup with name_three -- it "
                    "reads the global arrivals ledger directly, which has "
                    "no per-name-file structure to narrow further."
                )
            ledger = self.csvpaths.file_manager.files_root_manifest
            by_name = [e for e in ledger if e.get("named_file_name") == root_major]
            matched = self._filter_ledger_by_gate_chain(by_name, status_chain)
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

        bare_field_call = self._bare_definition_field_call(name_one)
        if bare_field_call is not None:
            # ":on_arrival()"/":sources()" bare -- settled 2026-08-12,
            # David: an arrival activation lives in the named-file's own
            # definition.json, it "doesn't go to the version level" --
            # confirmed by direct testing that the value is identical
            # regardless of which version a :name(...)+pointer combo
            # narrowed to (SOURCE == "definition" means _extract_data()
            # never reads result.uuid for these), so requiring either
            # was a real inconsistency with :definition() itself, which
            # already gets this same bare treatment. No :name(...)/
            # version needed at all -- matches :definition()'s own
            # precedent exactly, this just extracts one key from it
            # instead of returning the whole file.
            home = self.csvpaths.file_manager.named_file_home(root_major)
            path = Nos(home).join("definition.json")
            return ReferenceResults3(results=[ReferenceResult3(path=path, uuid=None)])

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
                raise ReferenceException3(
                    f"FilesReferenceFinder3 does not yet support combining a "
                    f"bare ':manifest():{manifest_field_call.name}()' lookup "
                    "with name_three -- it already reads a field from every "
                    "matched entry on its own."
                )
            manifest = self.csvpaths.file_manager.get_manifest(root_major)
            return ReferenceResults3(
                results=[
                    ReferenceResult3(path=e["file"], uuid=e["uuid"]) for e in manifest
                ]
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
            manifest = self.csvpaths.file_manager.get_manifest(root_major)
            selected = self._apply_pointer(pointer_call, manifest)
            if selected is None:
                return ReferenceResults3(results=[])
            return ReferenceResults3(
                results=[ReferenceResult3(path=selected["file"], uuid=selected["uuid"])]
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
                "FilesReferenceFinder3 does not support functions attached "
                "directly to name_one -- put the version-selecting function in "
                "name_three instead."
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
        elif self._is_bare_home_reference(name_one):
            # ':home()' as name_one's entire content -- a zero-level
            # selector, added 2026-08-12, mirroring RESULTS' own
            # ':home()' (David: keep functions meaning the same thing
            # across datatypes). Unlike RESULTS, this does NOT fall out
            # for free -- name_one can never be empty for FILES (the
            # grammar requires something after the last "."), so there
            # is no pre-existing "no pattern" code path for a bare
            # pointer to piggyback on the way RESULTS' bare pointer did.
            # Reuses the existing exact-length _matches machinery with
            # an EMPTY pattern (already correctly requires zero
            # intermediate segments, i.e. file_home == root_major's own
            # home directory exactly) -- no new matching primitive
            # needed. Does not collide with ':home()'s ordinary job as
            # a field accessor in name_three (SOURCE == "manifest",
            # reading the "file_home" key off a matched candidate) --
            # different position, different code path, and bare
            # ':home()' in name_one was previously unreachable/
            # undefined (only SOURCE == "definition" functions get bare
            # treatment via _bare_definition_field_call).
            candidates = self._candidates_for_name(root_major, [])
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
            # shape is not yet supported (redundant by construction --
            # there is nothing left to narrow).
            call = name_one.path[0]
            if reference.name_three is not None:
                raise ReferenceException3(
                    f"FilesReferenceFinder3 does not yet support combining "
                    f"a bare ':{call.name}(...)' lookup with name_three -- "
                    "it already identifies one specific version on its own."
                )
            function_cls = ReferenceFunctionFactory.get_registered_class(call.name)
            key = function_cls.KEY.get(Reference3.FILES)
            manifest = self.csvpaths.file_manager.get_manifest(root_major)
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
            # :flatten()/:groups()/:home()/selector-when-argued) or by
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
                    "FilesReferenceFinder3 does not support functions "
                    "attached directly to name_one -- put the version-"
                    "selecting function in name_three instead."
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
                return ReferenceResults3(
                    results=[
                        ReferenceResult3(path=c["file"], uuid=c["uuid"])
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
            if name_three.functions:
                raise ReferenceException3(
                    "FilesReferenceFinder3 does not yet support a literal "
                    "name_three body combined with trailing functions "
                    "(e.g. ':manifest()') -- no worked example establishes "
                    "what that combination should mean yet."
                )
            # a literal fingerprint body reduces to exactly one version,
            # same as a real pointer would -- the '#worksheet' marker
            # (name_one.name_two, carried through unchanged below) is
            # satisfied by this reduction just as well as by a real
            # POINTER function; no separate check needed here.
            matched = next(
                (c for c in candidates if c.get("fingerprint") == name_three.body),
                None,
            )
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
        if name_three.body is not None:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support a literal name_three "
                "body -- name_three must resolve to a pointer function "
                "(:first()/:last()/:index(n))."
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
            # generalized 2026-10-18 (was: a ':fingerprint()'-specific,
            # hand-written check, settled 2026-08-13) -- :uuid() became
            # a second SELECTOR_WHEN_ARGUED function needing the
            # identical guard once its own ARG_TYPES widened, so this
            # is now registry-driven instead of hardcoding a function
            # name. See _reject_selector_arg_outside_its_bare_form()'s
            # own docstring.
            self._reject_selector_arg_outside_its_bare_form(f)
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        if name_one.name_two is not None and not pointers:
            raise ReferenceException3(
                "FilesReferenceFinder3 requires a version-selecting "
                "pointer (:first()/:last()/:index(n)) alongside the "
                "'#worksheet' marker (name_two) -- there is no single "
                "version to read a worksheet from otherwise."
            )
        has_manifest = any(f.name == "manifest" for f in built)
        has_field_function = self._find_field_function_call(built) is not None
        has_all = any(f.name == "all" for f in built)
        lower_call, upper_call = self._range_calls_from_built(built)
        has_range = lower_call is not None or upper_call is not None
        from_is_date = to_is_date = False
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
            # shared _apply_manifest_date_range(). Mixing the two modes
            # in one lower/upper pair is rejected -- not because
            # it is meaningless (e.g.
            # ":from(:date('2025-01-01')):to(:index(10))" is a
            # reasonable ask: "10 versions starting from this date"),
            # but because it is AMBIGUOUS and undecided which of at
            # least two readings is meant -- is the index bound
            # absolute position in the full version list, or relative
            # to wherever the date bound starts matching? Nothing here
            # picks one, so mixing is rejected until that anchor
            # semantics question is deliberately settled, not attempted
            # here for lack of a driving use case.
            from_bound = self._range_bound(lower_call) if lower_call is not None else None
            to_bound = self._range_bound(upper_call) if upper_call is not None else None
            # TimeWindowFunction3 (":year()"/":date(...)"/etc, compendium
            # 6.27, added 2026-10-17) is date-mode too, same as a plain
            # string -- _range_bound() returns it as-is now, not
            # unwrapped to a raw value (see its own docstring).
            from_is_date = isinstance(from_bound, (str, TimeWindowFunction3))
            to_is_date = isinstance(to_bound, (str, TimeWindowFunction3))
            if (from_bound is not None and to_bound is not None) and (
                from_is_date != to_is_date
            ):
                raise ReferenceException3(
                    "FilesReferenceFinder3 does not support mixing index-"
                    "mode and date-mode range bounds in the same range."
                )
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

        if partitioned and (has_range or bare_time_window is not None):
            # ':from()'/':to()' (or a bare time-component function, same
            # reasoning, added 2026-10-17) combined with ':all()'/
            # ':groups()' grouping -- split into its own check 2026-09-25
            # (was previously merged into the :manifest() check just
            # below, giving a confusing "combining with :manifest()"
            # error even when no :manifest() was present at all,
            # confirmed live -- see the bucket list). Still rejected, not
            # built: the range-applying code just below (`if has_range:
            # candidates = self._apply_range(...)`) operates on the
            # POOLED candidate list, before partitioning by file_home --
            # "the last N versions" would mean the last N pooled across
            # every group, not the last N WITHIN each group, the same
            # AMBIGUOUS-reading concern RESULTS' own identical rejection
            # cites (does "last 2" mean per-group or pooled-then-split --
            # nothing here picks one). No driving use case has asked for
            # either reading, so this stays a clear rejection rather than
            # a guess, matching RESULTS' own precedent exactly.
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support combining "
                "':all()'/':groups()' grouping with ':from()'/':to()' or "
                "a bare time-component function -- resolve the grouped "
                "versions on their own first."
            )

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

        if bare_time_window is not None:
            # Gap 1 -- see this method's own comment above. `partitioned`
            # combined with a bare time window already raised above, so
            # this never runs concurrently with the by_file_home
            # partition branch below.
            candidates = self._apply_bare_time_window_to_manifest(
                candidates, bare_time_window
            )
        elif has_range:
            # narrow to the RANGE first -- a pointer riding alongside it
            # (below) then reduces that range, not the full candidate
            # set, same as RESULTS' own run-level range does. `partitioned`
            # combined with `has_range` already raised above, so this
            # never runs concurrently with the by_file_home partition
            # branch below.
            if from_is_date or to_is_date:
                candidates = self._apply_manifest_date_range(
                    candidates, lower_call, upper_call
                )
            else:
                candidates = self._apply_range(candidates, lower_call, upper_call)

        if pointers:
            if partitioned:
                # one independent reduction per distinct file_home, not
                # one pooled answer across all of them -- mirrors
                # _query_star_traversal's own is_grouped/is_deep_grouped
                # branch, scoped to this one named-file's own candidates
                # instead of every named-file's.
                by_file_home = {}
                for entry in candidates:
                    by_file_home.setdefault(entry["file_home"], []).append(entry)
                selected_candidates = []
                for file_home in sorted(by_file_home):
                    selected = self._apply_pointer(pointers[0], by_file_home[file_home])
                    if selected is not None:
                        selected_candidates.append(selected)
            else:
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

        return ReferenceResults3(
            results=[
                ReferenceResult3(
                    path=c["file"], uuid=c["uuid"], identity=name_one.name_two
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

        ':home()' and ':definition()' as name_one's own content -- added
        2026-08-27 (FILES '*' traversal generalization bucket-list
        entry), closing three of that entry's four identified gaps (the
        fourth, a predicate argument to filter by, is separately unbuilt
        -- see the predicate-argument bucket-list entry). Two independent
        shapes, both METADATA_FILE (definition.json is never versioned,
        so there is no "which version" left for name_three to narrow --
        combining either shape with name_three is rejected):
        - bare ':definition()' alone -- every named-file's own
          definition.json, one result per named-file, regardless of
          whether it has any zero-level registration at all.
        - ':home()' with ':definition()' chained onto it -- the SAME
          per-named-file definition.json lookup, but FILTERED to only
          named-files that have at least one zero-level ("no template")
          registration, per the concrete worked example that motivated
          this ("$*.files.:home():definition(:on_arrival(:not_none()))"
          -- "which named-files have on_arrival set," restricted to
          plain, non-templated registrations). ':home()' here is a
          filter, not the placeholder-value role it plays bare -- it has
          nothing to be a placeholder FOR, since ':definition()' does not
          vary by version/path the way a pointer's target would.
        A bare ':home()' with nothing chained onto it (no ':definition()')
        is a separate, third shape -- see the is_home branch below -- and
        falls through to the ordinary candidate/pointer machinery every
        other bare shape uses, since it is FIRST_PARTY-style path
        narrowing (an empty, zero-level pattern), not a metadata-file
        read.
        """
        name_one = reference.name_one
        if name_one.name_two is not None:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support the '#worksheet' "
                "marker (name_two)."
            )
        is_home = self._is_home_prefixed_reference(name_one)
        is_bare_definition = self._is_bare_definition_reference(name_one)
        definition_call = self._chained_definition_call(name_one)
        if is_bare_definition or (is_home and definition_call is not None):
            if reference.name_three is not None:
                raise ReferenceException3(
                    "FilesReferenceFinder3 does not yet support combining "
                    "':definition()' with name_three during '*' traversal "
                    "-- definition.json is not versioned, there is no "
                    "version to select."
                )
            names = self._matching_names(
                self.csvpaths.file_manager.named_file_names, name_filter
            )
            if is_home:
                names = [
                    name for name in names if self._candidates_for_name(name, [])
                ]
                if definition_call.arg is not None:
                    # generic predicate-argument filtering -- added
                    # 2026-10-17, closing the predicate-argument bucket-
                    # list entry's own worked example ("which named-files
                    # have on_arrival set"). self._build(definition_call)
                    # recursively builds the nested ':on_arrival(...)'
                    # chain AND runs Definition3.check_valid() (which
                    # cross-validates that the nested call is SOURCE ==
                    # "definition" with a PredicateFunction3 arg -- see
                    # its own docstring) before this ever filters
                    # anything, so field_call here is already a real,
                    # validated Function3 instance.
                    field_call = self._build(definition_call).arg
                    names = [
                        name
                        for name in names
                        if self._matches_definition_field_predicate(
                            name, field_call
                        )
                    ]
            results = []
            for name in names:
                home = self.csvpaths.file_manager.named_file_home(name)
                path = Nos(home).join("definition.json")
                results.append(ReferenceResult3(path=path, uuid=None))
            return ReferenceResults3(
                results=results,
                # Rule 1 (manifest_field_functions_proposal.md): resolving
                # full METADATA_FILE content for more than one entity at
                # once is illegal -- more than one named-file's own
                # definition.json is exactly that case, same as :manifest()
                # already flags via has_manifest/len(selected_candidates)
                # below. query() itself still returns every match; only
                # resolve_from() raises if a caller actually tries to
                # resolve more than one of these at once.
                ambiguous_content_read=len(results) > 1,
            )

        is_grouped = self._is_bare_all_reference(name_one)
        is_flattened = self._is_bare_flatten_reference(name_one)
        is_deep_grouped = self._is_bare_groups_reference(name_one)
        partitioned = is_grouped or is_deep_grouped
        if is_grouped:
            candidates = []
            for name in self._matching_names(
                self.csvpaths.file_manager.named_file_names, name_filter
            ):
                candidates.extend(self._candidates_for_name(name, [Star3()]))
        elif is_flattened or is_deep_grouped:
            candidates = []
            for name in self._matching_names(
                self.csvpaths.file_manager.named_file_names, name_filter
            ):
                candidates.extend(self._all_candidates_for_name(name))
        elif is_home:
            # bare ':home()', nothing chained onto it -- the zero-level
            # ("no template") placeholder, exactly like the literal-root
            # case's own is_bare_home_reference branch in query(), just
            # gathered across every named-file instead of one. Not
            # partitioned: an empty pattern is still a POOL-mode narrowing
            # (one level, just zero segments), the same peer relationship
            # a literal/'*' pattern already has to '*' traversal's own
            # bare-path POOL mode above -- a terminal pointer picks one
            # overall winner by time across every named-file's zero-level
            # version, it does not pick one winner per named-file (that
            # is what ':all()' is for).
            if name_one.functions:
                raise ReferenceException3(
                    "FilesReferenceFinder3 does not yet support chaining "
                    f":{name_one.functions[0].name}() onto ':home()' "
                    "during '*' traversal -- only ':definition()' is "
                    "supported so far."
                )
            candidates = []
            for name in self._matching_names(
                self.csvpaths.file_manager.named_file_names, name_filter
            ):
                candidates.extend(self._candidates_for_name(name, []))
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
            ledger = self.csvpaths.file_manager.files_root_manifest
            return ReferenceResults3(
                results=[
                    ReferenceResult3(path=e["file_path"], uuid=e["uuid"])
                    for e in ledger
                    if name_filter is None
                    or re.search(name_filter, e["named_file_name"])
                ]
            )
        else:
            if name_one.functions:
                # same settled restriction as query()'s own literal-root
                # branch (not-yet-supported sweep #3), for '*' traversal.
                raise ReferenceException3(
                    "FilesReferenceFinder3 does not support functions "
                    "attached directly to name_one for '*' traversal -- put "
                    "the version-selecting function in name_three instead."
                )
            pattern = self._compile_path_pattern(name_one.path)
            candidates = []
            for name in self._matching_names(
                self.csvpaths.file_manager.named_file_names, name_filter
            ):
                candidates.extend(self._candidates_for_name(name, pattern))

        name_three = reference.name_three
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

        if name_three.body is not None:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support a literal name_three "
                "body -- name_three must resolve to a pointer function "
                "(:first()/:last()/:index(n))."
            )
        built = self._build_chain(name_three.functions)
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        has_manifest = any(f.name == "manifest" for f in built)
        field_call = self._find_field_function_call(built)
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
            # case -- only "neither a pointer, nor a field accessor, nor
            # :manifest()" is still a genuine "nothing to resolve"
            # rejection.
            if field_call is None and not has_manifest:
                raise ReferenceException3(
                    "FilesReferenceFinder3 requires name_three to resolve to "
                    "exactly one pointer function (:first()/:last()/:index(n)) "
                    "when traversing every named-file with '*'."
                )
            return ReferenceResults3(
                results=[
                    ReferenceResult3(path=c["file"], uuid=c["uuid"])
                    for c in candidates
                ],
                ambiguous_content_read=(
                    has_manifest and field_call is None and len(candidates) > 1
                ),
            )
        pointer = pointers[0]

        if partitioned:
            by_file_home = {}
            for entry in candidates:
                by_file_home.setdefault(entry["file_home"], []).append(entry)
            selected_candidates = []
            for file_home in sorted(by_file_home):
                selected = self._apply_pointer(pointer, by_file_home[file_home])
                if selected is not None:
                    selected_candidates.append(selected)
        else:
            pooled = sorted(candidates, key=lambda e: e["time"])
            selected = self._apply_pointer(pointer, pooled)
            selected_candidates = [selected] if selected is not None else []

        return ReferenceResults3(
            results=[
                ReferenceResult3(path=c["file"], uuid=c["uuid"])
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
                and field_call is None
                and len(selected_candidates) > 1
                and not partitioned
            ),
        )

    def _candidates_for_name(self, name: str, pattern: list) -> list:
        """every manifest entry for one named-file whose file_home
        matches `pattern` relative to that name's own home directory --
        the per-name-file work shared by the literal-root_major path,
        '*' traversal's pool mode, and both ':all()' branches (which
        also match this exact-one-level pattern, just with the results
        partitioned rather than pooled afterward)."""
        manifest = self.csvpaths.file_manager.get_manifest(name)
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
        manifest = self.csvpaths.file_manager.get_manifest(name)
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
        manifest = self.csvpaths.file_manager.get_manifest(name)
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
        manifest = self.csvpaths.file_manager.get_manifest(name)
        home = self.csvpaths.file_manager.named_file_home(name).rstrip("/")
        home_parts = pathu.parts(home)
        return [
            entry
            for entry in manifest
            if pathu.parts(entry["file_home"])[: len(home_parts)] == home_parts
        ]

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
        \"Registration failed\"):named_file_name(\"orders\")" ("select
        named-files registrations for orders that failed").

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
        which IS generic).

        Every member (the leading ':status()' and any chained field
        accessors) must carry an argument and declare a real
        `KEY`/`LEDGER_KEY` entry for FILES -- that same per-entry
        lookup is what `FilesReferenceFinder3._filter_ledger_by_gate_
        chain()` uses to read each one directly off a raw ledger
        dict."""
        if len(name_one.path) != 1 or not isinstance(name_one.path[0], FunctionCall3):
            return None
        if name_one.path[0].name != "status" or name_one.path[0].arg is None:
            return None
        calls = [name_one.path[0], *name_one.functions]
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
    def _filter_ledger_by_gate_chain(ledger: list, chain: list) -> list:
        """every global-ledger entry matching ALL of `chain`'s own
        GATE arguments (AND-combined) -- e.g. ':status("Registration
        failed"):named_file_name("orders")' keeps only entries where
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

    @staticmethod
    def _ledger_entry_result_path(entry: dict) -> str:
        """the real path to use for a `ReferenceResult3` built from a
        raw global-ledger entry -- added 2026-10-18, caught live before
        shipping: `ReferenceResult3` itself forbids a None/empty path,
        but a "Registration failed" entry's own "file_path" is always
        None (the registration never got that far -- confirmed against
        `file_manager.py`'s own `_registration_failed()`, which never
        sets `file_path`/`file_home`/`file_name` at all). Falls back to
        "origin_path" (the attempted source file -- the one real path
        a failure entry DOES always carry) when "file_path" is empty;
        raises clearly, rather than letting `ReferenceResult3`'s own
        generic error leak through confusingly, if somehow neither is
        present."""
        path = entry.get("file_path") or entry.get("origin_path")
        if not path:
            raise ReferenceException3(
                "FilesReferenceFinder3 found a global arrivals ledger "
                "entry with neither a 'file_path' nor an 'origin_path' "
                "to report -- cannot build a result from it."
            )
        return path

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
    def _is_bare_home_reference(name_one) -> bool:
        """same shape as _is_bare_all_reference/_is_bare_flatten_
        reference/_is_bare_groups_reference, for ':home()' -- a zero-
        level selector when it is name_one's entire content (settled
        2026-08-12). Structurally exclusive with all three siblings."""
        return (
            not name_one.functions
            and len(name_one.path) == 1
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name == "home"
            and name_one.path[0].arg is None
        )

    @staticmethod
    def _is_home_prefixed_reference(name_one) -> bool:
        """true when name_one's path is exactly a single, argument-less
        ':home()' call -- UNLIKE _is_bare_home_reference, this does NOT
        also require name_one.functions to be empty, since ':home()' is
        legal here either bare (the zero-level placeholder, see
        _query_star_traversal's own is_home branch) or with exactly one
        ':definition()' chained onto it (the filtered-definition-lookup
        shape, see _chained_definition_call) -- '*' traversal only,
        added 2026-08-27 alongside that pair of shapes."""
        return (
            len(name_one.path) == 1
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name == "home"
            and name_one.path[0].arg is None
        )

    @staticmethod
    def _is_bare_definition_reference(name_one) -> bool:
        """true when name_one's entire content is a single, argument-
        less ':definition()' call, with no trailing function chain --
        the '*'-traversal counterpart to _is_bare_pointer_reference's
        identical literal-root check (added 2026-08-27, see
        _query_star_traversal's own early METADATA_FILE branch)."""
        return (
            not name_one.functions
            and len(name_one.path) == 1
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name == "definition"
            and name_one.path[0].arg is None
        )

    @staticmethod
    def _chained_definition_call(name_one) -> "FunctionCall3 | None":
        """returns the ':definition()' FunctionCall3 when it is the ONE
        thing chained onto name_one.functions (e.g. the "'home()':
        ':definition()'" shape ':home():definition()'), else None. Added
        2026-08-27 alongside _is_home_prefixed_reference -- the two are
        meant to be checked together (is_home and this both non-None) to
        recognize the filtered-definition-lookup shape specifically,
        rather than any other function someone might try to chain onto
        ':home()' during '*' traversal (still rejected, see the is_home
        branch's own functions check).

        No longer requires `call.arg is None` -- widened 2026-10-17 so
        this also recognizes ':home():definition(:on_arrival(:not_none()))'
        (the predicate-argument filtering shape, see query()'s own
        handling of a non-None arg here and Definition3.check_valid()
        for the real argument-shape validation, which this method does
        not attempt -- it only identifies the call, same as every other
        _is_X/._chained_X sibling in this file leaves argument-shape
        checks to the caller or to build()/check_valid()."""
        if len(name_one.functions) != 1:
            return None
        call = name_one.functions[0]
        if isinstance(call, FunctionCall3) and call.name == "definition":
            return call
        return None

    def _matches_definition_field_predicate(self, name: str, field_call) -> bool:
        """true if `name`'s own definition.json has `field_call`'s own
        field, and that value satisfies `field_call.arg`'s own predicate
        (e.g. ':not_none()') -- the generic predicate-argument filtering
        mechanism, added 2026-10-17 (deferred-work bucket list's own
        "Predicate-argument field accessors" entry). `field_call` is
        already a real, validated Function3 instance by the time this
        is called (Definition3.check_valid() already confirmed it is
        SOURCE == "definition" with a PredicateFunction3 arg, see
        query()'s own call site) -- this just reads the value and tests
        it, the exact same KEY-driven extraction the ordinary bare-
        field-accessor read already uses (see _extract_data()'s own
        "use_definition" branch), reused here rather than duplicated.
        Deliberately NOT bespoke to ':on_arrival()' -- any current or
        future SOURCE == "definition" field accessor works here for
        free, since nothing about this method's own logic names one."""
        function_cls = ReferenceFunctionFactory.get_registered_class(
            field_call.name
        )
        key_path = function_cls.KEY.get(Reference3.FILES)
        config = self.csvpaths.file_manager.describer.get_config(name)
        entry = config.model_dump(exclude_none=True)
        value = self._extract_field_value(entry, key_path)
        return field_call.arg.matches(value)

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
        rather than guessed at."""
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
        return call

    @staticmethod
    def _bare_definition_field_call(name_one) -> "FunctionCall3 | None":
        """returns the field-accessor FunctionCall3 when name_one's
        entire content is a single function whose registered class is
        SOURCE == "definition" (":on_arrival()"/":sources()"/etc.), OR
        whose BARE_SOURCE == "definition" (currently only ":template()"
        -- added 2026-08-26, see Template3's own docstring: bare/no-
        pointer means "the current default," genuinely a different
        resource than SOURCE == "manifest"'s own matched-version
        snapshot) -- these values live in the named-file's own
        definition.json, not any particular file/version's manifest
        entry, so (like ":definition()" itself) they need no
        :name(...)/matched-version context to resolve. An argument is
        fine here too (e.g. ":source_port(\"email\")" -- added
        2026-08-26 for the arg-keyed sources.<name>.* fields, see
        SourcePort3's own KEY docstring): the arg parameterizes the KEY
        lookup itself, not which version matched, so it does not need a
        candidate any more than an argument-less definition field does.
        None for every other shape, including a plain SOURCE ==
        "manifest" field accessor with no BARE_SOURCE (":uuid()"/
        ":time()"/etc.), which DOES vary by which version matched and
        still needs a real candidate."""
        if name_one.functions or len(name_one.path) != 1:
            return None
        segment = name_one.path[0]
        if not isinstance(segment, FunctionCall3):
            return None
        function_cls = ReferenceFunctionFactory.get_registered_class(segment.name)
        if function_cls is not None and (
            function_cls.SOURCE == "definition"
            or function_cls.BARE_SOURCE == "definition"
        ):
            return segment
        return None

    def _extract_data(self, result: ReferenceResult3):
        reference = self.ref.parsed
        log_call = self._bare_log_call(reference)
        if log_call is not None:
            return self._read_log_file(result.path, log_call.arg)
        if (
            reference.name_three is None
            and self._chained_definition_call(reference.name_one) is not None
        ):
            # ':home():definition()' chained during '*' traversal --
            # added 2026-08-27, covers both bare and (widened 2026-10-17)
            # predicate-argued (':home():definition(:on_arrival(
            # :not_none()))') forms. Checked here, BEFORE resolve_kind is
            # even read, rather than as a branch inside the `kind ==
            # METADATA_FILE` block below (where it used to live, and
            # still would work for the BARE form) -- a predicate-argued
            # nested field accessor makes resolve_kind's own generic
            # nested-arg walk classify the WHOLE reference as
            # METADATA_FIELD (a nested SOURCE == "definition" call
            # triggers the same default rule an ordinary bare field read
            # does), not METADATA_FILE. Widening the `kind ==
            # METADATA_FILE` guard below to also admit METADATA_FIELD was
            # tried first and confirmed LIVE to be unsafe for FILES
            # (unlike the analogous, safe widening already shipped for
            # RESULTS' :errors():idchain(...) GATE) -- it let ORDINARY
            # field reads during '*' traversal (e.g. ":all():last()
            # :uuid()", already METADATA_FIELD by resolve_kind) also
            # reach this block, where Rule 1b's own unconditional
            # "Star3 root_major + result.uuid is not None" re-derive-by-
            # uuid branch incorrectly intercepted them, returning the
            # whole manifest entry instead of the uuid field value (9
            # tests caught this immediately). Checking this specific
            # shape FIRST, before `kind` is even computed, sidesteps the
            # whole question -- result.path is already the matched
            # named-file's own definition.json path, set by
            # _query_star_traversal's own early METADATA_FILE branch,
            # regardless of which form matched there.
            return self._read_well_known_file(result.path)
        if (
            reference.name_three is None
            and not isinstance(reference.root_major, Star3)
            and result.uuid is not None
            and self._name_one_pointer(reference.name_one) is not None
        ):
            # compendium 5.21's "name_one, file pointer" shape -- a lone
            # pointer (:first()/:last()/:index(n)) directly in name_one
            # implies :manifest(), same as the explicit ':manifest()'+
            # pointer shape just below (_pointer_before_manifest)
            # already means. Checked here, BEFORE resolve_kind is read,
            # for the same reason the _chained_definition_call check
            # just above is: resolve_kind's own generic classification
            # has nothing to go on here (the pointer itself carries no
            # metadata_kind() of its own, unlike an explicit
            # ':manifest()' call), so it would otherwise default to
            # FIRST_PARTY and never reach the re-derive-by-uuid logic
            # the kind == METADATA_FILE block below uses for every
            # other shape that selects one manifest entry this way.
            manifest = self.csvpaths.file_manager.get_manifest(reference.root_major)
            return self._find_manifest_entry_by_uuid(manifest, result.uuid)
        kind = reference.resolve_kind
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
                not isinstance(reference.root_major, Star3)
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
                manifest = self.csvpaths.file_manager.get_manifest(
                    reference.root_major
                )
                return self._find_manifest_entry_by_uuid(manifest, result.uuid)
            if isinstance(reference.root_major, Star3) and result.uuid is not None:
                # Rule 1b -- a pointer already reduced the global ledger
                # to one entry in query(); re-derive it the same way the
                # per-entity branch below does, just against the ledger
                # instead of a named-file's own manifest.
                ledger = self.csvpaths.file_manager.files_root_manifest
                return self._find_manifest_entry_by_uuid(ledger, result.uuid)
            if (
                not isinstance(reference.root_major, Star3)
                and self._pointer_before_manifest(reference, "manifest") is not None
                and result.uuid is not None
            ):
                # symmetry fix, added 2026-10-16 -- the literal-root_major
                # counterpart to Rule 1b just above: query()'s own new
                # branch already ordinal-selected one entry out of THIS
                # named-file's own manifest.json; re-derive it here by
                # uuid, same pattern as every other METADATA_FILE branch
                # in this method.
                manifest = self.csvpaths.file_manager.get_manifest(
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
                manifest = self.csvpaths.file_manager.get_manifest(
                    reference.root_major
                )
                return self._find_manifest_entry_by_uuid(manifest, result.uuid)
        if kind == Reference3.METADATA_FIELD:
            is_bare_field_call = reference.name_three is None
            if not is_bare_field_call:
                field_call = self._find_field_function_call(
                    reference.name_three.functions
                )
            else:
                # a bare, SOURCE == "definition" field accessor occupying
                # name_one's entire content (":on_arrival()"/":sources()"),
                # OR a bare BARE_SOURCE == "definition" field accessor
                # (":template()" -- added 2026-08-26, see Template3's own
                # docstring) -- settled 2026-08-12/2026-08-26, see
                # query()'s own comment. Never reads result.uuid below for
                # a plain SOURCE == "definition" function (result.uuid
                # being None here is fine for those); a BARE_SOURCE
                # function reached here specifically because NO version
                # was selected at all, same reasoning.
                field_call = self._bare_definition_field_call(reference.name_one)
                if field_call is None:
                    # ':manifest():uuid()'-style, chained onto a bare
                    # ':manifest()' in name_one rather than definition-
                    # sourced -- added 2026-08-28, see query()'s/
                    # _query_star_traversal()'s own comment on this
                    # shape. result.uuid is real here (query() built it
                    # from the actual matched manifest entry), so the
                    # ordinary manifest-entry-by-uuid read below applies
                    # unchanged -- only the "which manifest to search"
                    # step (just below) needs to know about '*' root.
                    field_call = self._bare_manifest_field_call(
                        reference.name_one
                    )
            if field_call is not None:
                function_cls = ReferenceFunctionFactory.get_registered_class(
                    field_call.name
                )
                if function_cls.SOURCE == "computed":
                    # never stored -- comes straight from the already-
                    # resolved reference, no manifest/definition read at
                    # all. see function_3.py's SOURCE comment.
                    return self._compute_field(field_call.name, reference)
                if field_call.name == "named_file_name":
                    # a real, stored field at RESULTS/RESULT scope, but at
                    # FILES scope this is just the already-known resolved
                    # name -- reading it back from the manifest would be
                    # redundant, so it is computed here instead, same
                    # reasoning as the "computed" SOURCE branch above.
                    return reference.root_major
                key_path = function_cls.KEY.get(reference.datatype)
                key_path = self._apply_key_arg(key_path, field_call.arg)
                use_definition = function_cls.SOURCE == "definition" or (
                    is_bare_field_call and function_cls.BARE_SOURCE == "definition"
                )
                if use_definition:
                    config = self.csvpaths.file_manager.describer.get_config(
                        reference.root_major
                    )
                    entry = config.model_dump(exclude_none=True)
                    return self._extract_field_value(entry, key_path)
                if isinstance(reference.root_major, Star3):
                    # ':manifest():uuid()' during '*' traversal -- added
                    # 2026-08-28. root_major is the '*' token itself
                    # here, not a real name, so get_manifest() cannot be
                    # called with it -- read the same global arrivals
                    # ledger query()'s own '*'-traversal branch built
                    # these results from instead (this shape is the
                    # only way a name_three-less, root_major-is-Star3
                    # METADATA_FIELD read reaches this far -- the
                    # ordinary name_three field-accessor position still
                    # unconditionally rejects '*' traversal in
                    # _query_star_traversal(), so this branch is never
                    # reached for that shape).
                    manifest = self.csvpaths.file_manager.files_root_manifest
                else:
                    manifest = self.csvpaths.file_manager.get_manifest(
                        reference.root_major
                    )
                entry = self._find_manifest_entry_by_uuid(manifest, result.uuid)
                return self._extract_field_value_with_ledger_fallback(
                    entry=entry,
                    key_path=key_path,
                    function_cls=function_cls,
                    datatype=reference.datatype,
                    ledger_entry_getter=lambda: self._find_manifest_entry_by_uuid(
                        self.csvpaths.file_manager.files_root_manifest, result.uuid
                    ),
                )
        raise ReferenceException3(
            f"FilesReferenceFinder3 does not yet support resolve_kind={kind!r} "
            "-- only :manifest()/:definition() and registered field-accessor "
            "functions are wired up as metadata-file/field functions so far."
        )

    def _compute_field(self, name: str, reference: "Reference3") -> object:
        """values for SOURCE == "computed" field-accessor functions --
        never read from a manifest/definition, always derived from the
        already-resolved reference. See function_3.py's SOURCE comment
        and named_file_home_3.py."""
        if name == "named_file_home":
            return self.csvpaths.file_manager.named_file_home(reference.root_major)
        raise ReferenceException3(
            f"FilesReferenceFinder3 has no computed-field handling for :{name}()"
        )

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
