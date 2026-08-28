from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos
from csvpath.util.xlsx.xlsx_reader_helper import XlsxReaderHelper

from .functions.function_3 import Function3
from .functions.reference_function_factory_3 import ReferenceFunctionFactory
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
    #    *which version*. A literal name_three body (bypassing a
    #    pointer function entirely) is not yet supported. ":manifest()"
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

        name_one = reference.name_one
        if (
            name_one.name_two is not None
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name != "name"
        ):
            # '#worksheet' only means anything against a literal named-
            # file path (there is one specific file to have worksheets
            # in) -- ':name("...")' is path-BUILDING (a literal name),
            # same as any other literal path segment, so it is exempt
            # here same as it is from _is_bare_function_only's own
            # "bare marker" test; a bare context-setter/pointer/marker
            # function occupying name_one's entire content (':manifest()',
            # ':all()', ':home()', etc.) has no file of its own to read
            # a worksheet from.
            raise ReferenceException3(
                "FilesReferenceFinder3 does not support the '#worksheet' "
                "marker (name_two) combined with a bare context-setter/"
                "pointer function in name_one -- it only applies to a "
                "literal named-file path."
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

        if name_one.functions:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support functions attached "
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
        elif self._is_bare_fingerprint_reference(name_one):
            # bare ':fingerprint("hash...")' -- added 2026-08-13. Content-
            # hash identity does not care which file/path slot a version
            # happens to be registered under (unlike ':name()', which
            # matches file_home, a path identity, not a content one), so
            # this searches the WHOLE named-file's manifest directly --
            # every file_home/path, not just a pattern-matched subset --
            # for the entry whose own "fingerprint" field matches.
            # Confirmed against FileRegistrar's real write path: the
            # version file itself is literally stored/named by its own
            # fingerprint, so an exact match here is reliable. At most
            # one match is expected in practice (two DIFFERENT logical
            # files sharing byte-identical content is the only way to
            # get more than one) -- not specially guarded against.
            #
            # Returns the matched version(s) directly, with their real
            # path/uuid, and does NOT fall through to the shared "no
            # name_three -> dedupe to a directory, uuid=None" logic below
            # -- unlike ':name()', a fingerprint already identifies one
            # SPECIFIC version, there is no further "which version"
            # narrowing step to defer. name_three combined with this
            # shape is not yet supported (redundant by construction --
            # there is nothing left to narrow).
            if reference.name_three is not None:
                raise ReferenceException3(
                    "FilesReferenceFinder3 does not yet support combining "
                    "a bare ':fingerprint(...)' lookup with name_three -- "
                    "it already identifies one specific version on its own."
                )
            manifest = self.csvpaths.file_manager.get_manifest(root_major)
            fingerprint = name_one.path[0].arg
            matched = [e for e in manifest if e.get("fingerprint") == fingerprint]
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
            pattern = self._compile_path_pattern(name_one.path)
            candidates = self._candidates_for_name(root_major, pattern)

        name_three = reference.name_three
        if name_three is None:
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

        if name_three.body is not None:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support a literal name_three "
                "body -- name_three must resolve to a pointer function "
                "(:first()/:last()/:index(n))."
            )
        built = ReferenceFunctionFactory.build_chain(name_three.functions)
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
            if f.name == "fingerprint" and f.arg is not None:
                # ':fingerprint(...)' only takes an argument in its bare,
                # name_one lookup form (settled 2026-08-13) -- riding
                # alongside a matched version here, in its ordinary
                # field-accessor position, it takes none (it reads
                # whatever the matched version's own fingerprint IS, it
                # does not filter by a given one). Raising here avoids
                # an arg being silently ignored, which ARG_TYPES = (str,)
                # would otherwise allow through unnoticed.
                raise ReferenceException3(
                    "FilesReferenceFinder3's ':fingerprint()' only takes "
                    "an argument in its bare, name_one lookup form -- "
                    "riding alongside a matched version in name_three, "
                    "it takes none."
                )
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
        from_call = next((f for f in built if f.name == "from"), None)
        to_call = next((f for f in built if f.name == "to"), None)
        has_range = from_call is not None or to_call is not None
        from_is_date = to_is_date = False
        from_bound = to_bound = None
        if has_range:
            # ':from()'/':to()' as a name_three version range -- added
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
            # in one ':from()'/':to()' pair is rejected -- not because
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
            from_bound = self._range_bound(from_call) if from_call is not None else None
            to_bound = self._range_bound(to_call) if to_call is not None else None
            from_is_date = isinstance(from_bound, str)
            to_is_date = isinstance(to_bound, str)
            if (from_bound is not None and to_bound is not None) and (
                from_is_date != to_is_date
            ):
                raise ReferenceException3(
                    "FilesReferenceFinder3 does not support mixing index-"
                    "mode and date-mode ':from()'/':to()' bounds in the "
                    "same range."
                )
            if from_is_date:
                self._validate_date_format(from_bound)
            if to_is_date:
                self._validate_date_format(to_bound)
        # the old "at least one recognized category present" gate that
        # used to live here is now unreachable, not just redundant: the
        # _check_position() loop above already guarantees every element
        # of `built` (which is itself guaranteed non-empty, see that
        # loop's own comment) is one of exactly the categories checked
        # below (pointers/has_manifest/has_field_function/has_all/
        # has_range cover the complete set of name_three-legal FILES
        # functions), so at least one of them is always true here.

        if partitioned and (has_range or (pointers and (has_manifest or has_field_function))):
            # mirrors ResultsReferenceFinder3's own ':all()'-grouping
            # restriction (settled 2026-08-11 there): grouping (one-
            # level ':all()' or any-depth ':groups()') plus :manifest()/
            # a field-accessor is an under-specified interaction, not
            # decided -- resolve the grouped versions on their own
            # first, rather than guessing what "the manifest entry of
            # every group's own latest version, all at once" should even
            # resolve to.
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support combining "
                "':all()'/':groups()' grouping with :manifest() or a "
                "field-accessor function -- resolve the grouped versions "
                "on their own first."
            )

        if has_range:
            # narrow to the RANGE first -- a pointer riding alongside it
            # (below) then reduces that range, not the full candidate
            # set, same as RESULTS' own run-level range does. `partitioned`
            # combined with `has_range` already raised above, so this
            # never runs concurrently with the by_file_home partition
            # branch below.
            if from_is_date or to_is_date:
                candidates = self._apply_manifest_date_range(
                    candidates, from_bound, to_bound
                )
            else:
                candidates = self._apply_range(candidates, from_call, to_call)

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
            ambiguous_content_read=has_manifest and len(selected_candidates) > 1,
        )

    def _query_star_traversal(self, reference: Reference3) -> ReferenceResults3:
        """root_major == "*" -- query across every named-file, not just
        one. Four distinct semantics, corrected/extended 2026-08-12 to
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

        Deliberately narrow for now, matching only the spec's own worked
        examples: combining '*'/':flatten()'/':groups()' traversal with
        :manifest()/a field-accessor function in name_three is not yet
        supported -- those all assume exactly one already-known manifest
        to re-read in _extract_data(), which does not hold when a result
        could have come from any of several named-files' manifests.

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
        if is_bare_definition or (
            is_home and self._chained_definition_call(name_one) is not None
        ):
            if reference.name_three is not None:
                raise ReferenceException3(
                    "FilesReferenceFinder3 does not yet support combining "
                    "':definition()' with name_three during '*' traversal "
                    "-- definition.json is not versioned, there is no "
                    "version to select."
                )
            names = self.csvpaths.file_manager.named_file_names
            if is_home:
                names = [
                    name for name in names if self._candidates_for_name(name, [])
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
            for name in self.csvpaths.file_manager.named_file_names:
                candidates.extend(self._candidates_for_name(name, [Star3()]))
        elif is_flattened or is_deep_grouped:
            candidates = []
            for name in self.csvpaths.file_manager.named_file_names:
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
            for name in self.csvpaths.file_manager.named_file_names:
                candidates.extend(self._candidates_for_name(name, []))
        else:
            if name_one.functions:
                raise ReferenceException3(
                    "FilesReferenceFinder3 does not yet support functions "
                    "attached directly to name_one for '*' traversal -- put "
                    "the version-selecting function in name_three instead."
                )
            pattern = self._compile_path_pattern(name_one.path)
            candidates = []
            for name in self.csvpaths.file_manager.named_file_names:
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
        built = ReferenceFunctionFactory.build_chain(name_three.functions)
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        unsupported = (
            any(f.name == "manifest" for f in built)
            or self._find_field_function_call(built) is not None
        )
        if unsupported:
            raise ReferenceException3(
                "FilesReferenceFinder3 does not yet support combining '*' "
                "traversal with :manifest() or a field-accessor function -- "
                "only a plain pointer (:first()/:last()/:index(n)) is "
                "supported so far."
            )
        if not pointers:
            raise ReferenceException3(
                "FilesReferenceFinder3 requires name_three to resolve to "
                "exactly one pointer function (:first()/:last()/:index(n)) "
                "when traversing every named-file with '*'."
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
            ]
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
        return [
            entry
            for entry in manifest
            if entry["file_home"].rstrip("/").startswith(home)
        ]

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
        branch's own functions check)."""
        if len(name_one.functions) != 1:
            return None
        call = name_one.functions[0]
        if isinstance(call, FunctionCall3) and call.name == "definition" and call.arg is None:
            return call
        return None

    @staticmethod
    def _is_bare_fingerprint_reference(name_one) -> bool:
        """same shape as _is_bare_home_reference, for ':fingerprint(...)'
        -- settled 2026-08-13, but the OPPOSITE arg requirement: WITH an
        arg (the hash to search for), not without -- a bare, argument-
        less ':fingerprint()' has no candidate to read the field off of
        at this position, so it is deliberately NOT recognized here and
        falls through to the ordinary "not yet supported" rejection."""
        return (
            not name_one.functions
            and len(name_one.path) == 1
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name == "fingerprint"
            and name_one.path[0].arg is not None
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
            if self._is_bare_pointer_reference(
                reference, "manifest"
            ) or self._is_bare_pointer_reference(reference, "definition"):
                # result.path is already the manifest.json/definition.json
                # path itself (set by query()'s _query_well_known_file()
                # branch above). Also covers bare ':definition()' during
                # '*' traversal -- _is_bare_pointer_reference does not
                # look at root_major, and _query_star_traversal's own
                # early METADATA_FILE branch sets result.path the same
                # way for that shape (added 2026-08-27).
                return self._read_well_known_file(result.path)
            if (
                reference.name_three is None
                and self._chained_definition_call(reference.name_one) is not None
            ):
                # ':home():definition()' chained during '*' traversal --
                # added 2026-08-27. result.path is already the matched
                # named-file's own definition.json path, set by
                # _query_star_traversal's own early METADATA_FILE branch.
                return self._read_well_known_file(result.path)
            if isinstance(reference.root_major, Star3) and result.uuid is not None:
                # Rule 1b -- a pointer already reduced the global ledger
                # to one entry in query(); re-derive it the same way the
                # per-entity branch below does, just against the ledger
                # instead of a named-file's own manifest.
                ledger = self.csvpaths.file_manager.files_root_manifest
                return self._find_manifest_entry_by_uuid(ledger, result.uuid)
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
        file_home = entry["file_home"].rstrip("/")
        if not file_home.startswith(home):
            return False
        rel = file_home[len(home) :].lstrip("/")
        segments = rel.split("/") if rel else []
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
        file_home = entry["file_home"].rstrip("/")
        if not file_home.startswith(home):
            return False
        rel = file_home[len(home) :].lstrip("/")
        segments = rel.split("/") if rel else []
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
        file_home = entry["file_home"].rstrip("/")
        if not file_home.startswith(home):
            return False
        rel = file_home[len(home) :].lstrip("/")
        segments = rel.split("/") if rel else []
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
