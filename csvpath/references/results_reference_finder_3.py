import json
import re

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

from .functions.function_3 import Function3
from .functions.filters.idchain_3 import Idchain3
from .functions.reference_function_factory_3 import ReferenceFunctionFactory
from .reference_3 import FunctionCall3, Reference3, Star3
from .reference_exceptions_3 import ReferenceException3
from .reference_finder_3 import ReferenceFinder3
from .reference_results_3 import ReferenceResult3, ReferenceResults3

#
# first pass, deliberately narrow, mirroring Files/CsvpathsReferenceFinder3's
# scoping approach -- but results is its own shape, the STRUCTURE table's
# "deepest hierarchy": name_one is a path-like prefix search AS WELL AS the
# version (run) selector, both together (unlike files, which splits "which
# file"/name_one from "which version"/name_three; unlike csvpaths, which has
# no real path at all). name_three identifies one csvpath statement's own
# result directory within the selected run(s).
#
#  - root_major is a literal named-results name (the same name as the named-
#    paths group that was run), or "*" (every named-results group). "*" has
#    two exceptions carved out before general traversal (Rule 1a/1b, a
#    bare/ordinal-indexed :manifest() reads the global archive ledger); any
#    other use of "*" goes through _query_star_traversal(), which mirrors
#    query()'s own dispatch tree (bare/':flatten()'/':all()'/literal-'*'
#    path, ':groups()' still deferred) across every group instead of one
#    fixed home -- see that method's own docstring for the full history
#    (2026-08-14 through 2026-08-19) and why ':manifest()' alone stays
#    unsupported. name_three (an instance selector) composes with every
#    shape too. A pointer is now OPTIONAL everywhere here (settled
#    2026-08-19, matching RESULTS' own literal-root precedent and
#    FilesReferenceFinder3's star traversal, which never requires one
#    either) -- absence means every matched run comes back, unreduced.
#    ':all()' partitions by the COMPOSITE (named-results group, 1-level
#    template value) key when a pointer IS present, resolving a real
#    meaning-collision -- see "THE ':all()' MEANING COLLISION AT STAR
#    TRAVERSAL" in references_notes/notes/normative_reference_examples.txt
#    for the worked example that settled it.
#  - name_one has TWO legal shapes, matching the spec's own examples
#    ("$acme.results.:all()"/"$acme.results.:last()" alongside
#    "$acme.results.customers/2025:first()"):
#      (a) bare/function-only, no literal path at all (mirrors csvpaths --
#          the sole path "segment" is itself a version-selecting function,
#          e.g. :all()/:first()/:last()/:index(n)). A bare POINTER alone
#          (no :all()/:flatten()/:groups()) means zero-level only -- direct
#          children of the group's own root, no template -- settled
#          2026-08-10. A bare ':all()' means exactly one level, wildcarded
#          -- the same restriction '*' has, and unaffected by whether a
#          pointer follows it (settled 2026-08-11, correcting an earlier
#          version that let a pointer-less ':all()' fall through to
#          any-depth behavior). ':flatten()' pools any depth into one
#          answer; ':groups()' partitions any depth into one answer per
#          distinct value observed (added 2026-08-12, alongside FILES'
#          own ':groups()' -- David: keep functions meaning the same
#          thing across datatypes) -- see each function's own docstring.
#      (b) literal/"*"/:name("...") path segments (same semantics as files
#          -- see ReferenceFinder3._compile_path_pattern) PLUS its own
#          trailing function chain -- narrows to runs whose own prefix
#          (see _discover_run_homes/_matches_prefix below) matches.
#    Either way, every matching run is pooled into ONE flat list first
#    (mirroring how a bare "*" already flattens across every match for
#    files, rather than reducing per matched prefix separately), and the
#    combined chain's at most one pointer function (:first()/:last()/
#    :index(n)) reduces that WHOLE pool to one run; absent, every pooled
#    run comes back unreduced -- for query()'s own purposes (just listing
#    paths/uuids). This is how "Name_one used alone == path to run dir"
#    (STRUCTURE table) is reached. The "#worksheet" marker (name_two,
#    files-only) is not meaningful here and is rejected. Resolving full
#    content (:manifest(), or an instance-level accessor -- see below) is
#    a stricter case: if no pointer narrows the pool and more than one run
#    matched, query() raises rather than pooling several runs' content --
#    settled 2026-08-07, see manifest_field_functions_proposal.md's
#    "Entity resolution and pooling" section. Listing (query() alone) is
#    unaffected either way.
#  - name_three, if present, is an identity lookup into the selected run's
#    own instance-directory listing (one subdirectory per csvpath statement,
#    named by that statement's identity -- same convention as csvpaths'
#    named_paths_identities) -- matched by identity string, or by :all() for
#    every instance in the run. A well-known instance-level file function
#    (:errors()/:vars()/:meta()/:data()/:unmatched(), or the arbitrary-named
#    :file("...")) may ride alongside the identity/:all() selector in the
#    same chain (e.g. "$acme.results.customers/2025:first().invoices:data()")
#    -- these functions never narrow/select anything themselves (ROLE is
#    VALUE, matching :manifest()/:definition()'s own corrected role), they
#    just say what to resolve to once an instance is already identified.
#    Resolving a matched instance with NO accessor present still gives None
#    (no default) -- only the identity/:all() selection was made, nothing
#    further was asked for. An accessor riding alongside :all() specifically
#    (rather than one specific identity) is illegal, for the same single-
#    entity reason as the run-level case above: :all() means every instance
#    in the run, each with its own separate well-known file on disk, so
#    reading their content all at once is exactly the "more than one entity"
#    case the rule forbids.
#
# storage facts this relies on (confirmed against ResultsManager/
# ResultsRegistrar/ResultRegistrar/ResultSerializer, and a real archive-root
# manifest.json entry David pasted, not assumed): there is no per-named-
# results-group manifest array the way files/csvpaths have -- but there IS
# a single, archive-wide manifest.json (one entry per csvpath-statement
# execution, across every named-paths group -- the same one the earlier
# run-ordering experiment found unreliable as an ORDERING source, owing to
# cross-group interleaving and stale entries for deleted runs). Each entry
# already carries "run_home", the exact, already-resolved absolute path a
# specific run's directory landed at, recorded at the moment that run
# happened -- discovery, not ordering: this sidesteps ever needing to
# know/guess a group's own template depth (which lives in the group's own
# template string, e.g. PathsManager.get_template_for_paths(), and can
# change over time or be overridden per-run -- neither matters here, since
# run_home already reflects whatever template was actually in effect for
# that specific run). Confirmed against v1/v2's own working equivalent
# (csvpath/util/references/results_tools/resolve_possibles.py), which uses
# this exact same manifest+run_home+existence-check approach rather than
# directory-walking. Stale entries are handled by an existence check
# (Nos(run_home).exists()), same as v2 does. Run directories are named
# "%Y-%m-%d_%H-%M-%S[_N]" (RunHomeMaker) -- the timestamp itself is
# fixed-width/zero-padded, so plain lexicographic sort is safe for it,
# but "_N" (RunHomeMaker.get_run_dir, appended starting at "_0" when a
# run collides with one already claimed for the same group+prefix
# within the same second -- confirmed by David not to be rare during
# test suite runs) is a plain, unpadded integer -- lexicographic sort
# of THAT alone is not safe ("_10" sorts before "_9" as strings). See
# _run_dir_sort_key(), used everywhere a list of run_home paths/
# segments needs true chronological order. Each run
# directory has its own manifest.json (a single dict; "run_uuid" identifies
# the run itself). Each run directory contains one subdirectory per csvpath
# statement, named by that statement's own identity
# (ResultSerializer.get_instance_dir), each with its own manifest.json (a
# single dict; "uuid" identifies that instance).
#


class ResultsReferenceFinder3(ReferenceFinder3):
    #
    # matches a run directory's disambiguating "_N" suffix (RunHomeMaker
    # -- appended starting at "_0" when a run collides with one already
    # claimed for the same group+prefix within the same second). Requires
    # the WHOLE tail after the last "_" to be digits, which the plain
    # "%H-%M-%S" timestamp tail (always containing "-") never is -- so
    # this only ever matches a genuine disambiguation suffix, never a
    # bare timestamp.
    #
    _RUN_SUFFIX_RE = re.compile(r"^(.*)_(\d+)$")

    @classmethod
    def _run_dir_sort_key(cls, run_home: str) -> tuple:
        """true chronological sort key for a run directory path or bare
        segment -- see this module's own docstring for why plain
        lexicographic sort of the full string is not safe once a "_N"
        disambiguation suffix is involved. A run with no suffix at all
        sorts before any suffixed collision for the same timestamp
        (suffixes start at "_0", so -1 correctly sorts before 0)."""
        seg = run_home.rstrip("/").rsplit("/", 1)[-1]
        m = cls._RUN_SUFFIX_RE.match(seg)
        if m:
            return (m.group(1), int(m.group(2)))
        return (seg, -1)

    def query(self) -> ReferenceResults3:
        reference = self.ref.parsed
        root_major = reference.root_major
        if isinstance(root_major, Star3):
            if self._is_bare_pointer_reference(reference, "manifest"):
                # Rule 1a (manifest_field_functions_proposal.md): "*" at
                # root_major combined with a bare :manifest() is the one
                # exception -- it resolves to the Archive Run Manifest,
                # the single global ledger at the archive root already
                # used internally by _discover_run_homes() to find every
                # run across every named-results group.
                archive = self.csvpaths.config.get(section="results", name="archive")
                return self._query_well_known_file(archive, "manifest.json")
            pointer_call = self._pointer_before_manifest(reference, "manifest")
            if pointer_call is not None:
                # Rule 1b -- a pointer riding before the bare :manifest()
                # (e.g. "$*.results.:last():manifest()") selects one
                # entry out of the global ledger by ordinal position,
                # instead of dumping the whole thing. the archive ledger
                # has no "uuid" key of its own (only "run_uuid" -- see
                # RunRegistrar.metadata_update()), so run_uuid is used as
                # the locator instead of the usual uuid.
                archive = self.csvpaths.config.get(section="results", name="archive")
                path = Nos(archive).join("manifest.json")
                ledger = self.csvpaths.results_manager.results_root_manifest
                selected = self._apply_pointer(pointer_call, ledger)
                if selected is None:
                    return ReferenceResults3(results=[])
                return ReferenceResults3(
                    results=[ReferenceResult3(path=path, uuid=selected["run_uuid"])]
                )
            return self._query_star_traversal(reference)

        name_one = reference.name_one
        if name_one.name_two is not None:
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not support the '#worksheet' "
                "marker (name_two) -- it is files-only."
            )

        home = self.csvpaths.results_manager.get_named_results_home(root_major)
        run_homes = [rh for rh, _ in self._discover_run_homes(root_major)]
        calls = self._combined_name_one_calls(name_one)
        # added 2026-08-14 -- the same fix already made for CSVPATHS'
        # _resolve_versions() and FILES' name_three chain: replaces
        # nothing here (there was no equivalent "at least one recognized
        # category" gate to redundantly cover), it CLOSES a real gap --
        # confirmed via direct testing before this fix that
        # "$acme.results.:last():webhooks()" (a function registered for
        # a DIFFERENT datatype entirely, not even results-relevant)
        # silently no-opped instead of raising, since every check below
        # only ever looks for SPECIFIC recognized names, never rejects
        # an unrecognized extra riding alongside them. Does not touch
        # name_one's own PATH-BUILDING segments (literal/'*'/:name()) --
        # those are already safe, validated separately and correctly by
        # the shared ReferenceFinder3._compile_path_pattern().
        for f in ReferenceFunctionFactory.build_chain(calls):
            self._check_position(f, Reference3.NAME_ONE, Reference3.RESULTS)
        pointer = self._pointer_from_calls(calls)
        is_grouped = any(
            isinstance(c, FunctionCall3) and c.name == "all" for c in calls
        )
        # group_key_for: set only when ':all()'/':groups()' partitions
        # candidates by observed value AND a pointer exists to reduce
        # each partition (David's three-templates example -- three
        # different one-level templates all group correctly by whatever
        # directory each run actually landed in, not by which template
        # produced it -- ':groups()' extends this to any depth, see
        # _group_key). Left None when there is no pointer -- grouping
        # only matters at the reduce step, so with no pointer the
        # "grouped" and "pooled" candidate sets are identical anyway.
        group_key_for = None

        if self._is_bare_function_only(name_one):
            is_flattened = any(
                isinstance(c, FunctionCall3) and c.name == "flatten" for c in calls
            )
            is_deep_grouped = any(
                isinstance(c, FunctionCall3) and c.name == "groups" for c in calls
            )
            if sum([is_grouped, is_flattened, is_deep_grouped]) > 1:
                raise ReferenceException3(
                    "ResultsReferenceFinder3 does not support combining "
                    "':all()'/':flatten()'/':groups()' -- each is its own "
                    "depth/grouping choice, not to be combined with another."
                )
            if is_grouped:
                # bare ':all()' -- exactly one level, wildcarded, peer of
                # a bare '*' (illegal on its own, but this is the same
                # one-level restriction) -- settled 2026-08-11,
                # regardless of whether a pointer follows. Corrected
                # from an earlier version that let a pointer-less
                # ':all()' fall through to ':flatten()'s any-depth
                # candidate set by mistake, mirroring csvpaths' own
                # depth-less ':all()' precedent -- which does not apply
                # here, since csvpaths has no path dimension at all to
                # be wrong about, but results does.
                pattern = [Star3()]
                candidates = [
                    rh for rh in run_homes if self._matches_prefix(rh, home, pattern)
                ]
                if pointer is not None:
                    group_key_for = {
                        rh: self._group_key(rh, home) for rh in candidates
                    }
            elif is_flattened:
                # ':flatten()', with or without a pointer -- every run
                # discovered for the group is a candidate, any depth, no
                # prefix narrowing.
                candidates = run_homes
            elif is_deep_grouped:
                # ':groups()' -- added 2026-08-12, the any-depth GROUP
                # peer of ':all()' (one-level GROUP)/':flatten()' (any-
                # depth POOL), built alongside FILES' own ':groups()' in
                # the same pass (David: keep functions meaning the same
                # thing across datatypes). Same any-depth candidate set
                # as ':flatten()' (no prefix-length restriction), but
                # partitioned by _group_key -- each run's FULL relative
                # path (not just its last segment, since two runs at
                # different depths could otherwise share a trailing
                # segment by coincidence and be wrongly conflated). A
                # zero-level (no-template) run gets the empty-tuple key
                # -- its own valid, distinct group, not a special case.
                candidates = run_homes
                if pointer is not None:
                    group_key_for = {
                        rh: self._group_key(rh, home) for rh in candidates
                    }
            else:
                # a plain pointer alone, e.g. "$acme.results.:last()" --
                # zero-level (direct children of the group's own root)
                # only, NOT "ignore depth entirely" -- settled
                # 2026-08-10. ':flatten()' above is the new home for
                # the any-depth case this used to cover. A bare
                # ':home()' ALONE (no pointer/:all()/:flatten() also
                # present) reaches this same branch and needs no
                # special-casing at all -- settled 2026-08-11: ':home()'
                # is a VALUE-role field accessor, never a POINTER, so
                # _pointer_from_calls() below naturally finds none,
                # leaving every zero-level candidate unreduced -- "every
                # run whose home is right here" (David's own framing).
                # The moment a real pointer joins the chain (either
                # order -- ":home():last()" or ":last():home()"), that
                # pointer reduces to one and ':home()' reverts to its
                # ordinary job (reading the field off whatever got
                # selected) -- no order-sensitivity trap, since nothing
                # here depends on which of the two is written first.
                # There is NO prefixed equivalent ("beta/:home()") --
                # considered and removed 2026-08-12: a literal prefix
                # segment with nothing trailing already means "every
                # run under this exact prefix, unreduced" (long-
                # standing, pre-dates this whole depth refactor --
                # confirmed "$acme.results.beta" and
                # "$acme.results.beta/:home()" give identical results
                # in every case tested). ':home()' is only load-bearing
                # at the bare/root position, where the grammar cannot
                # express "zero segments" any other way -- a literal
                # prefix already covers every other depth, so adding
                # ':home()' there would just be a second, more
                # confusing spelling of something that already has one
                # (David: explicit felt "more mysterious than the
                # default," and collided with the unrelated ":run_dir"
                # template token in a reader's head).
                candidates = [
                    rh for rh in run_homes if self._matches_prefix(rh, home, [])
                ]
        elif isinstance(name_one.path[-1], FunctionCall3) and name_one.path[
            -1
        ].name == "flatten":
            # a literal/wildcard prefix, then ':flatten()' as the last
            # segment, e.g. "beta/:flatten():last()" -- matches this
            # prefix, then anything, at any remaining depth, instead of
            # requiring an exact segment count the way a plain literal/
            # '*' pattern does.
            if name_one.path[-1].arg is not None:
                raise ReferenceException3(
                    "ResultsReferenceFinder3's ':flatten()' does not take "
                    "an argument."
                )
            prefix_pattern = self._compile_path_pattern(name_one.path[:-1])
            candidates = [
                rh
                for rh in run_homes
                if self._matches_prefix_at_least(rh, home, prefix_pattern)
            ]
        elif isinstance(name_one.path[-1], FunctionCall3) and name_one.path[
            -1
        ].name == "all":
            # a literal/wildcard prefix, then ':all()' as the last
            # segment, e.g. "beta/:all():last()" -- matches exactly one
            # level beyond the prefix (like "beta/*" would), grouped by
            # the run's own actual value at that position instead of
            # pooled.
            if name_one.path[-1].arg is not None:
                raise ReferenceException3(
                    "ResultsReferenceFinder3's ':all()' does not take an "
                    "argument."
                )
            pattern = self._compile_path_pattern(name_one.path[:-1]) + [Star3()]
            candidates = [
                rh for rh in run_homes if self._matches_prefix(rh, home, pattern)
            ]
            if pointer is not None:
                group_key_for = {
                    rh: self._group_key(rh, home, prefix_len=len(pattern) - 1)
                    for rh in candidates
                }
        elif isinstance(name_one.path[-1], FunctionCall3) and name_one.path[
            -1
        ].name == "groups":
            # a literal/wildcard prefix, then ':groups()' as the last
            # segment, e.g. "beta/:groups():last()" -- added 2026-08-12,
            # matches this prefix, then anything, at any remaining depth
            # (same candidate set as the prefixed ':flatten()' branch
            # above), grouped by everything beyond the fixed prefix
            # instead of pooled -- one result per distinct value observed
            # there, even when that remaining depth varies per run.
            if name_one.path[-1].arg is not None:
                raise ReferenceException3(
                    "ResultsReferenceFinder3's ':groups()' does not take "
                    "an argument."
                )
            prefix_pattern = self._compile_path_pattern(name_one.path[:-1])
            candidates = [
                rh
                for rh in run_homes
                if self._matches_prefix_at_least(rh, home, prefix_pattern)
            ]
            if pointer is not None:
                group_key_for = {
                    rh: self._group_key(rh, home, prefix_len=len(prefix_pattern))
                    for rh in candidates
                }
        else:
            pattern = self._compile_path_pattern(name_one.path)
            candidates = [
                rh for rh in run_homes if self._matches_prefix(rh, home, pattern)
            ]
        candidates = sorted(candidates, key=self._run_dir_sort_key)

        from_call, to_call = self._range_calls_from_calls(calls)
        if from_call is not None or to_call is not None:
            # ':from()'/':to()' as a run-level range -- added 2026-08-13,
            # e.g. "customers:from(:index(-3))" -- "the last three runs
            # with template customers." Stays a LIST (not reduced to
            # one) unless a real pointer also rides alongside it, same
            # as ':all()'/':groups()' already do -- the pointer, if
            # present, reduces the RANGE, not the full candidate set.
            #
            # Two independent MODES, picked by each bound's own value
            # type: index-mode (int/:index(n)) POSITIONALLY slices, via
            # the shared _apply_range(); date-mode (str/:date(...),
            # added the same day, David: "arrival and run order is even
            # more important than indexing") FILTERS by each run's own
            # arrival date instead, via _apply_date_range() below --
            # comparing POSITIONS would be meaningless for a date bound.
            # Mixing the two modes in one :from()/:to() pair is rejected
            # -- not because it is meaningless (e.g.
            # ":from(:date('2025-01-01')):to(:index(10))" is a
            # reasonable ask: "10 runs starting from this date"), but
            # because it is AMBIGUOUS and undecided which of at least
            # two readings is meant -- is the index bound absolute
            # position in the full candidate list, or relative to
            # wherever the date bound starts matching? Nothing here
            # picks one, so mixing is rejected until that anchor
            # semantics question is deliberately settled, not attempted
            # here for lack of a driving use case.
            if group_key_for:
                raise ReferenceException3(
                    "ResultsReferenceFinder3 does not yet support combining "
                    "':from()'/':to()' with ':all()'/':groups()' grouping."
                )
            from_bound = self._range_bound(from_call) if from_call is not None else None
            to_bound = self._range_bound(to_call) if to_call is not None else None
            from_is_date = isinstance(from_bound, str)
            to_is_date = isinstance(to_bound, str)
            if (from_bound is not None and to_bound is not None) and (
                from_is_date != to_is_date
            ):
                raise ReferenceException3(
                    "ResultsReferenceFinder3 does not support mixing index-"
                    "mode and date-mode ':from()'/':to()' bounds in the "
                    "same range."
                )
            if from_is_date or to_is_date:
                if from_is_date:
                    self._validate_date_format(from_bound)
                if to_is_date:
                    self._validate_date_format(to_bound)
                candidates = self._apply_date_range(candidates, from_bound, to_bound)
            else:
                candidates = self._apply_range(candidates, from_call, to_call)

        identity, match_all, accessor, _, range_bounds = self._name_three_selector(
            reference.name_three
        )
        has_manifest = any(
            seg.contains_function_named("manifest")
            for seg in calls
            if isinstance(seg, FunctionCall3)
        )
        wants_full_content = has_manifest or accessor is not None
        if group_key_for and (
            wants_full_content or self._find_field_function_call(calls) is not None
        ):
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not yet support combining "
                "':all()'/':groups()' grouping with :manifest() or a "
                "run-level field accessor -- resolve the grouped runs on "
                "their own first."
            )

        if group_key_for:
            # partition candidates by their own observed group key,
            # apply the pointer independently within each partition --
            # one result per distinct value observed. candidates is
            # already sorted by _run_dir_sort_key, so each partition
            # keeps correct arrival order internally.
            groups: dict = {}
            for rh in candidates:
                groups.setdefault(group_key_for[rh], []).append(rh)
            selected_runs = []
            for key in sorted(groups):
                selected = self._apply_pointer(pointer, groups[key])
                if selected is not None:
                    selected_runs.append(selected)
        elif pointer is not None:
            selected = self._apply_pointer(pointer, candidates)
            selected_runs = [selected] if selected is not None else []
        else:
            selected_runs = candidates
            if len(selected_runs) > 1 and wants_full_content:
                # Resolving full manifest/well-known-file content always
                # touches exactly one entity (settled 2026-08-07, see
                # manifest_field_functions_proposal.md's "Entity
                # resolution and pooling" section) -- more than one run
                # here needs a pointer to pick which one, whether the
                # content lives at the run level (:manifest()) or the
                # instance level (an accessor riding on name_three).
                raise ReferenceException3(
                    "ResultsReferenceFinder3 requires a pointer (:first()/"
                    ":last()/:index(n)) to pick one run when reading full "
                    "content and more than one run matches -- resolving "
                    "full content always touches exactly one entity."
                )

        if match_all and accessor is not None:
            # :all() pools every instance in the run -- each instance has
            # its own separate well-known file on disk, so this is the
            # same "more than one entity" case as above, just one level
            # down. A specific identity is still fine: that is already
            # exactly one instance.
            raise ReferenceException3(
                "ResultsReferenceFinder3 requires a specific statement "
                "identity, not :all(), to read full well-known-file "
                "content -- resolving full content always touches "
                "exactly one entity."
            )

        results = []
        for run_dir in selected_runs:
            results.extend(
                self._results_for_run(
                    run_dir, identity, match_all, range_bounds, accessor
                )
            )
        return ReferenceResults3(results=results)

    def _query_star_traversal(self, reference: Reference3) -> ReferenceResults3:
        """root_major == "*" -- query across every named-results group,
        not just one. Mirrors query()'s own dispatch tree (bare
        function-only / prefix+':flatten()' / prefix+':all()' /
        prefix+':groups()' / plain literal-'*' path), just computing
        each candidate's own home per its own group (via
        _discover_run_homes(None), which keeps each pair's group name
        specifically for this) instead of one fixed home -- added
        2026-08-19, closing the "literal/'*' path narrowing" gap this
        method used to reject outright. ':groups()' (any-depth GROUP)
        stays unsupported here, same as bare ':groups()' already was --
        no established per-GROUP-of-named-results-groups meaning exists
        for it yet, left for if/when a real use case asks. name_three
        (an instance selector) is now supported too (added 2026-08-19)
        -- _results_for_run() already does the identity/':all()'/range
        selection entirely from a real run directory, independent of
        group, so it composes with every shape above unchanged; the one
        real design point is the ':all()'-GROUPING-plus-content-
        accessor case, see _star_group_and_reduce()'s own comment.
        :manifest() combined with real narrowing is now supported too
        (fixed 2026-08-26, the "active next task" this whole depth-
        matrix pass used to defer) -- _star_run_selector_chain() allows
        it through the same validation as a field accessor, and
        _extract_data() now disambiguates a Rule-1a/1b global-ledger
        result from a genuine traversal-selected run by comparing
        result.path against the ledger's own known, fixed path, rather
        than the old, now-ambiguous "does it have a uuid" test (both
        shapes carry a real uuid once this composes with real
        narrowing) -- see _extract_data()'s own has_manifest branch.

        A pointer is now OPTIONAL in every shape above (settled
        2026-08-19, via _star_run_selector_chain()) -- absence means
        every matched run comes back, unreduced, the same meaning a
        missing pointer already has at every literal-root query() shape
        (none of them require one). Confirmed against the closest
        sibling datatype before making this change:
        FilesReferenceFinder3's own '*' traversal never requires a
        pointer either, in any of its four modes -- see this module's
        own top-of-file docstring for the full comparison, including
        CsvpathsReferenceFinder3's own partial (POOL-requires-it,
        GROUP-does-not) precedent, which this deliberately does NOT
        copy (RESULTS' own literal-root behavior and FILES both make it
        optional everywhere, a stronger and more directly relevant
        precedent than CSVPATHS' narrower one).

        Chronological order across every group cannot use a full-path
        string sort the way one group's own query() case can get away
        with (different groups' run directories live under different
        prefixes, so a full-path sort would sort by group name first,
        not by timestamp) -- _run_dir_sort_key() extracts just the
        trailing directory-name segment, AND handles that segment's own
        disambiguating "_N" suffix numerically rather than as a string
        (see this module's own docstring for why that suffix
        specifically cannot be sorted as a plain string).
        """
        name_one = reference.name_one
        if name_one.name_two is not None:
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not support the '#worksheet' "
                "marker (name_two) -- it is files-only."
            )
        identity, match_all, accessor, _, range_bounds = self._name_three_selector(
            reference.name_three
        )
        if match_all and accessor is not None:
            # same "more than one entity" rule the literal-root case
            # already enforces, unconditionally, regardless of run
            # count -- :all() at name_three means every instance in
            # whichever run(s) match, each with its own separate well-
            # known file on disk.
            raise ReferenceException3(
                "ResultsReferenceFinder3 requires a specific statement "
                "identity, not :all(), to read full well-known-file "
                "content -- resolving full content always touches "
                "exactly one entity."
            )

        if self._is_bare_function_only(name_one):
            calls = self._combined_name_one_calls(name_one)
            pointer, all_call, flatten_call = self._star_run_selector_chain(calls)
            if all_call is not None:
                # exactly one level, wildcarded -- the SAME [Star3()]
                # restriction bare ':all()' already applies for one
                # literal group, just computed per candidate's own
                # group home. Partitions by the COMPOSITE (group,
                # template-value) key -- see this method's own
                # docstring and normative_reference_examples.txt's "THE
                # ':all()' MEANING COLLISION AT STAR TRAVERSAL" section.
                partitioned = []
                for rh, group in self._discover_run_homes(None):
                    home = self.csvpaths.results_manager.get_named_results_home(
                        group
                    )
                    if self._matches_prefix(rh, home, [Star3()]):
                        partitioned.append(
                            (rh, (group, self._group_key(rh, home)))
                        )
                return self._star_group_and_reduce(
                    partitioned, pointer, identity, match_all, range_bounds, accessor
                )
            if flatten_call is not None:
                # any depth, every group -- _discover_run_homes(None)
                # already discovers across every group with no depth
                # restriction of its own (the zero-level restriction in
                # the else branch below is applied AFTER discovery, by
                # the _matches_prefix filter, not by discovery itself),
                # so no separate any-depth gathering logic is needed
                # here.
                run_homes = [rh for rh, _ in self._discover_run_homes(None)]
            else:
                # zero-level (direct children of each run's own group's
                # home) only -- same restriction the literal-root
                # query() case now applies to a plain bare pointer,
                # settled 2026-08-10.
                run_homes = [
                    rh
                    for rh, group in self._discover_run_homes(None)
                    if self._matches_prefix(
                        rh,
                        self.csvpaths.results_manager.get_named_results_home(group),
                        [],
                    )
                ]
            return self._star_pool_and_reduce(
                run_homes, pointer, identity, match_all, range_bounds, accessor
            )

        if isinstance(name_one.path[-1], FunctionCall3) and name_one.path[
            -1
        ].name == "flatten":
            # a literal/wildcard prefix, then ':flatten()' as the last
            # path segment, e.g. "beta/:flatten():last()" -- matches
            # this prefix (relative to each candidate's OWN group home),
            # then anything, at any remaining depth.
            if name_one.path[-1].arg is not None:
                raise ReferenceException3(
                    "ResultsReferenceFinder3's ':flatten()' does not take "
                    "an argument."
                )
            prefix_pattern = self._compile_path_pattern(name_one.path[:-1])
            calls = list(name_one.functions)
            pointer, _, _ = self._star_run_selector_chain(calls)
            run_homes = [
                rh
                for rh, group in self._discover_run_homes(None)
                if self._matches_prefix_at_least(
                    rh,
                    self.csvpaths.results_manager.get_named_results_home(group),
                    prefix_pattern,
                )
            ]
            return self._star_pool_and_reduce(
                run_homes, pointer, identity, match_all, range_bounds, accessor
            )

        if isinstance(name_one.path[-1], FunctionCall3) and name_one.path[
            -1
        ].name == "all":
            # a literal/wildcard prefix, then ':all()' as the last path
            # segment, e.g. "beta/:all():last()" -- matches exactly one
            # level beyond the prefix (relative to each candidate's OWN
            # group home), grouped by the COMPOSITE (group, observed-
            # value-at-that-position) key, same as the bare case above.
            if name_one.path[-1].arg is not None:
                raise ReferenceException3(
                    "ResultsReferenceFinder3's ':all()' does not take an "
                    "argument."
                )
            prefix = self._compile_path_pattern(name_one.path[:-1])
            pattern = prefix + [Star3()]
            calls = list(name_one.functions)
            pointer, _, _ = self._star_run_selector_chain(calls)
            partitioned = []
            for rh, group in self._discover_run_homes(None):
                home = self.csvpaths.results_manager.get_named_results_home(group)
                if self._matches_prefix(rh, home, pattern):
                    partitioned.append(
                        (
                            rh,
                            (
                                group,
                                self._group_key(
                                    rh, home, prefix_len=len(pattern) - 1
                                ),
                            ),
                        )
                    )
            return self._star_group_and_reduce(
                partitioned, pointer, identity, match_all, range_bounds, accessor
            )

        if isinstance(name_one.path[-1], FunctionCall3) and name_one.path[
            -1
        ].name == "groups":
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not yet support ':groups()' "
                "combined with '*' traversal -- no established per-GROUP-"
                "of-named-results-groups meaning exists yet, unlike the "
                "literal-root case's own ':groups()'."
            )

        # plain literal/'*' path, no trailing ':flatten()'/':all()'/
        # ':groups()' marker -- POOL mode, exact-length match (relative
        # to each candidate's OWN group home), reduced by the pointer.
        pattern = self._compile_path_pattern(name_one.path)
        calls = list(name_one.functions)
        pointer, _, _ = self._star_run_selector_chain(calls)
        run_homes = [
            rh
            for rh, group in self._discover_run_homes(None)
            if self._matches_prefix(
                rh, self.csvpaths.results_manager.get_named_results_home(group), pattern
            )
        ]
        return self._star_pool_and_reduce(
            run_homes, pointer, identity, match_all, range_bounds, accessor
        )

    def _star_run_selector_chain(self, calls: list) -> tuple:
        """validates a run-selecting combined function chain for '*'
        traversal, shared by every _query_star_traversal shape (bare
        and literal/'*'-prefixed alike) -- added 2026-08-19, factored
        out of what used to be inline-only-for-the-bare-case logic once
        the literal/'*'-prefixed shapes needed the identical validation.
        Returns (pointer, all_call, flatten_call); all_call/flatten_call
        are only ever non-None for the bare shape (calls includes
        name_one.path[0] itself there) -- for a prefixed shape, calls is
        just name_one.functions, and the ':all()'/':flatten()' marker
        lives in name_one.path[-1] instead, inspected separately by the
        caller, so it can never appear in `built` here; returning
        None/None for those callers is correct, not a missed case.
        A run-level field-accessor function (e.g. :uuid(),
        :named_paths_name() -- added 2026-08-18) is exempt from the
        non-pointer rejection below, same as ':all()'/':flatten()' are:
        _results_for_run() already builds each candidate's
        ReferenceResult3 from its own real run directory, independent
        of any group-name context, so resolving a field from it needs
        nothing star-traversal-specific.

        A pointer itself is now OPTIONAL here (changed 2026-08-19) --
        absence means "every matched run, unreduced," the SAME meaning
        a missing pointer already has at every literal-root query()
        shape (bare/':flatten()'/':all()' alike -- none of them require
        one there). Confirmed against the closest sibling datatype
        before making this change: FilesReferenceFinder3's own '*'
        traversal NEVER requires a pointer either, in any of its four
        modes (see its own _query_star_traversal docstring) -- a
        missing pointer there returns a deduped list of distinct
        file_home values. RESULTS does not need FILES' dedup-plus-
        uuid=None trick (each candidate here is already a distinct real
        run directory via _discover_run_homes()'s own dedup, so every
        unreduced result can carry its own real run uuid, not a
        placeholder). CsvpathsReferenceFinder3 is the outlier here, not
        the target precedent -- it requires a pointer in POOL/flatten
        mode but not GROUP/':all()' mode, an asymmetry noted but not
        touched (a separate, already-merged PR, not blocking anything
        needed here)."""
        built = ReferenceFunctionFactory.build_chain(calls)
        field_call = self._find_field_function_call(built)
        all_call = next((f for f in built if f.name == "all"), None)
        flatten_call = next((f for f in built if f.name == "flatten"), None)
        manifest_call = next((f for f in built if f.name == "manifest"), None)
        if all_call is not None and flatten_call is not None:
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not support combining "
                "':all()'/':flatten()' -- each is its own depth/grouping "
                "choice, not to be combined with another."
            )
        non_pointers = [
            f
            for f in built
            if f.ROLE != Function3.POINTER
            and f is not field_call
            and f is not flatten_call
            and f is not all_call
            and f is not manifest_call
        ]
        if non_pointers:
            raise ReferenceException3(
                f"ResultsReferenceFinder3 does not yet support "
                f":{non_pointers[0].name}() combined with '*' traversal -- "
                "only a bare pointer (:first()/:last()/:index(n)), "
                "optionally combined with ':all()'/':flatten()', :manifest(), "
                "and/or a run-level field-accessor function (e.g. :uuid()), "
                "is supported so far."
            )
        pointer = self._pointer_from_calls(calls)
        return pointer, all_call, flatten_call

    def _star_pool_and_reduce(
        self,
        run_homes: list,
        pointer,
        identity: str | None,
        match_all: bool,
        range_bounds: tuple | None,
        accessor,
    ) -> ReferenceResults3:
        """POOL mode's shared tail -- added 2026-08-19, alongside
        _star_group_and_reduce(), factored out once name_three needed
        threading through every star-traversal shape identically. A
        missing pointer (added 2026-08-19, see _star_run_selector_chain()'s
        own comment for why) means every matched run comes back,
        unreduced -- which can now be MORE than one run, so the same
        "more than one candidate + content accessor" guard the GROUP
        case already needs applies here too."""
        run_homes = sorted(run_homes, key=self._run_dir_sort_key)
        if pointer is None:
            if len(run_homes) > 1 and accessor is not None:
                raise ReferenceException3(
                    "ResultsReferenceFinder3 does not yet support combining "
                    "unreduced '*' traversal (no pointer, more than one "
                    "matched run) with a name_three content accessor -- "
                    "resolve the matched runs on their own first."
                )
            results = []
            for run_dir in run_homes:
                results.extend(
                    self._results_for_run(
                        run_dir, identity, match_all, range_bounds, accessor
                    )
                )
            return ReferenceResults3(results=results)
        selected = self._apply_pointer(pointer, run_homes)
        if selected is None:
            return ReferenceResults3(results=[])
        return ReferenceResults3(
            results=self._results_for_run(
                selected, identity, match_all, range_bounds, accessor
            )
        )

    def _star_group_and_reduce(
        self,
        partitioned: list,
        pointer,
        identity: str | None,
        match_all: bool,
        range_bounds: tuple | None,
        accessor,
    ) -> ReferenceResults3:
        """GROUP mode's shared tail (":all()", bare or literal/'*'-
        prefixed) -- added 2026-08-19. `partitioned`: list of
        (run_home, composite_key) pairs. Unlike POOL mode, a pointer
        here can still select MORE than one run overall (one per
        partition) -- so a name_three CONTENT accessor (:errors()/
        :vars()/etc, as opposed to a poolable field accessor like
        :uuid()) is rejected outright here, mirroring the literal-root
        query() case's own "':all()'/':groups()' grouping does not
        combine with :manifest() or a run-level field accessor"
        restriction, narrowed to the piece that actually applies here:
        a name_three CONTENT accessor reading full file content is "one
        entity" per the same rule content accessors are held to
        everywhere else in this file, and grouping can produce several.
        A name_three FIELD accessor (e.g. ".invoices:uuid()") is NOT
        rejected -- confirmed live against the already-shipped literal-
        root precedent (":all():last().invoices:uuid()" resolves fine,
        poolable, one result per matched run) before writing this.

        A missing pointer (added 2026-08-19) means every matched run
        comes back, unreduced -- mirroring CsvpathsReferenceFinder3's
        own already-shipped ':all()'-with-no-pointer precedent
        (extends the filtered manifest, ungrouped) exactly: once there
        is no pointer to reduce a partition to one, the partitioning
        itself stops mattering for the OUTPUT (every member of every
        partition just comes back), so this degenerates to the same
        "list everything, unreduced" case _star_pool_and_reduce()
        already handles -- delegated there directly rather than
        duplicating that logic."""
        if accessor is not None and pointer is not None:
            # the content-accessor rejection only applies when grouping
            # can still yield more than one run (pointer present, one
            # per partition) -- the no-pointer case below reuses
            # _star_pool_and_reduce()'s own equivalent guard instead,
            # since it is really the same "list everything, unreduced"
            # case once there is no pointer.
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not yet support combining "
                "':all()' grouping with a name_three content accessor -- "
                "resolve the grouped runs on their own first."
            )
        if pointer is None:
            return self._star_pool_and_reduce(
                [rh for rh, _ in partitioned],
                None,
                identity,
                match_all,
                range_bounds,
                accessor,
            )
        groups: dict = {}
        for rh, key in partitioned:
            groups.setdefault(key, []).append(rh)
        results = []
        for key in sorted(groups):
            candidates = sorted(groups[key], key=self._run_dir_sort_key)
            selected = self._apply_pointer(pointer, candidates)
            if selected is not None:
                results.extend(
                    self._results_for_run(
                        selected, identity, match_all, range_bounds, accessor
                    )
                )
        return ReferenceResults3(results=results)

    _JSON_ACCESSOR_FILES = {
        "errors": "errors.json",
        "vars": "vars.json",
        "meta": "meta.json",
    }
    _BYTES_ACCESSOR_FILES = {
        "data": "data.csv",
        "unmatched": "unmatched.csv",
    }

    def _extract_data(self, result: ReferenceResult3):
        reference = self.ref.parsed
        name_one_calls = self._combined_name_one_calls(reference.name_one)
        has_manifest = any(
            seg.contains_function_named("manifest")
            for seg in name_one_calls
            if isinstance(seg, FunctionCall3)
        )
        if isinstance(reference.root_major, Star3) and has_manifest:
            # Rule 1a/1b vs. a genuine traversal-selected run both reach
            # here now (fixed 2026-08-26) -- both carry a real, non-None
            # uuid once _query_star_traversal supports :manifest()
            # combined with real narrowing (:all()/:flatten()/a literal
            # prefix), so `result.uuid is not None` can no longer tell
            # them apart (the exact gap this whole branch used to have,
            # tracked in the bucket list as "the active next task").
            # Compare result.path against the ledger's own known, fixed
            # path instead: Rule 1a/1b's own query() branches always set
            # result.path to the archive-root manifest.json itself,
            # never a run directory, so this is a reliable, structural
            # test rather than a data-dependent guess.
            archive = self.csvpaths.config.get(section="results", name="archive")
            ledger_path = Nos(archive).join("manifest.json")
            if result.path == ledger_path:
                if result.uuid is not None:
                    # Rule 1b -- a pointer already reduced the global
                    # ledger to one entry in query(); re-derive it by
                    # run_uuid (the archive ledger's own locator -- see
                    # query()).
                    ledger = self.csvpaths.results_manager.results_root_manifest
                    return next(
                        (e for e in ledger if e["run_uuid"] == result.uuid), None
                    )
                # global-ledger case (Rule 1a) -- query()'s
                # _query_well_known_file() branch already pointed
                # result.path at the archive-root manifest.json itself,
                # so read it directly rather than joining "manifest.json"
                # onto it again (the ordinary, per-group has_manifest
                # branch below does that join, but only because it deals
                # with a run directory, not a file).
                return self._read_well_known_json(result.path)
            # a genuine traversal-selected run (result.path is that run's
            # own directory, not the ledger) -- fall through to the
            # ordinary has_manifest branch immediately below, which
            # already does exactly the right thing (read that
            # directory's own manifest.json) regardless of whether
            # root_major was literal or '*'.
        if has_manifest:
            # :manifest() rides beside the run-selecting pointer in
            # name_one (e.g. "$acme.results.customers/2025:first()
            # :manifest()") -- the STRUCTURE table's own "Resolve
            # terminating at name_one, with file pointer: results:
            # contents of manifest.json" row.
            #
            # Files/csvpaths share ONE manifest.json array across every
            # version of a named-file/named-paths group, so resolving
            # several matched versions' :manifest() means filtering that
            # one shared array down to several entries (see
            # _find_manifest_entry_by_uuid). Results is different: each
            # matched run has its OWN separate manifest.json file on
            # disk -- reading more than one would mean opening more than
            # one file, which query()'s own guard above already forbids
            # (a pointer is required whenever more than one run would
            # otherwise match). So by the time we get here, result.path
            # is always exactly one run's directory, and we just read
            # its own manifest.json directly (below), the same as any
            # other per-result payload via the ordinary resolve() loop.
            if reference.name_three is not None:
                raise ReferenceException3(
                    "ResultsReferenceFinder3 does not support combining "
                    ":manifest() on name_one with name_three -- resolve "
                    "the run's own manifest on its own, without a "
                    "further instance selector."
                )
            return self._read_well_known_json(
                Nos(result.path).join("manifest.json")
            )

        run_field_call = self._find_field_function_call(name_one_calls)
        if run_field_call is not None:
            # a registered field-accessor (e.g. :run_uuid()) riding
            # beside the run-selecting pointer in name_one, the same
            # slot :manifest() rides in -- extracts one key from the
            # run's own manifest.json instead of the whole dict. Same
            # "no name_three" restriction as :manifest(), for the same
            # reason: asking for both a run-level field and a specific
            # instance at once is not a supported combination.
            #
            # also correctly serves root_major='*' now (added
            # 2026-08-18, once _query_star_traversal started allowing a
            # field accessor through) with no extra logic needed here --
            # result.path is already the matched run's own real
            # directory regardless of which group it came from (see
            # _results_for_run), so reading its own manifest.json needs
            # no group-name context at all, unlike CSVPATHS' equivalent
            # fix, which does.
            if reference.name_three is not None:
                raise ReferenceException3(
                    "ResultsReferenceFinder3 does not support combining "
                    "a run-level field accessor on name_one with "
                    "name_three -- resolve the run's own field on its "
                    "own, without a further instance selector."
                )
            function_cls = ReferenceFunctionFactory.get_registered_class(
                run_field_call.name
            )
            entry = self._read_well_known_json(
                Nos(result.path).join("manifest.json")
            )
            key_path = function_cls.KEY.get(Reference3.RESULTS)
            return self._extract_field_value_with_ledger_fallback(
                entry=entry,
                key_path=key_path,
                function_cls=function_cls,
                datatype=Reference3.RESULTS,
                ledger_entry_getter=lambda: self._find_archive_ledger_entry(
                    ledger=self.csvpaths.results_manager.results_root_manifest,
                    run_uuid=entry.get("run_uuid") if entry else None,
                ),
            )

        kind = reference.resolve_kind
        if kind in (Reference3.METADATA_FILE, Reference3.METADATA_FIELD):
            # both land here: :errors() alone classifies as METADATA_FILE,
            # :errors(:idchain(...)) classifies as METADATA_FIELD (a
            # nested pointer-like arg -- see Reference3.resolve_kind) --
            # _read_accessor already handles the idchain-filtering
            # internally based on accessor.arg, so both kinds resolve
            # identically from here.
            _, _, accessor, field_call, _ = self._name_three_selector(
                reference.name_three
            )
            if accessor is not None:
                return self._read_accessor(result.path, accessor)
            if field_call is not None:
                # a registered field-accessor (e.g. :uuid()) riding
                # alongside the identity/:all() selector, the same slot
                # :errors() etc. ride in -- extracts one key from the
                # matched instance's own manifest.json instead of a
                # well-known file.
                function_cls = ReferenceFunctionFactory.get_registered_class(
                    field_call.name
                )
                entry = self._read_well_known_json(
                    Nos(result.path).join("manifest.json")
                )
                key_path = function_cls.KEY.get(Reference3.RESULT)
                return self._extract_field_value_with_ledger_fallback(
                    entry=entry,
                    key_path=key_path,
                    function_cls=function_cls,
                    datatype=Reference3.RESULT,
                    ledger_entry_getter=lambda: self._find_archive_ledger_entry(
                        ledger=self.csvpaths.results_manager.results_root_manifest,
                        run_uuid=entry.get("run_uuid") if entry else None,
                        identity=entry.get("instance_identity") if entry else None,
                    ),
                )
        if kind != Reference3.FIRST_PARTY:
            raise ReferenceException3(
                f"ResultsReferenceFinder3 does not yet support "
                f"resolve_kind={kind!r} -- only :errors()/:vars()/:meta()/"
                ":data()/:unmatched()/:file() are wired up as metadata-"
                "file functions so far."
            )
        # a run directory (no name_three) or an instance directory matched
        # by identity/:all() with no accessor riding alongside has no
        # single unambiguous payload -- "no default", per "creating
        # references v3.txt"'s resolve table.
        return None

    @staticmethod
    def _find_archive_ledger_entry(
        *, ledger: list, run_uuid: str, identity: str | None = None
    ) -> dict | None:
        """Table 7 (the Archive Run Manifest, RESULTS' own global ledger)
        is per-statement-execution -- one entry per csvpath statement
        run, keyed by "run_uuid" + "identity", not a single "uuid" the
        way FILES/CSVPATHS ledgers are (see
        ReferenceFinder3._find_manifest_entry_by_uuid) -- added
        2026-08-26 to wire the field-accessor ledger-fallback mechanism
        (Function3.LEDGER_KEY) into RESULTS, closing Table 7 gap
        flagged in the bucket list.

        `identity` is optional: the run-scope fallback fields this was
        built for (archive_name/archive_path/named_files_root/
        named_paths_root) are the SAME value across every statement in
        one run (confirmed against run_registrar.py -- they are written
        once per run_uuid, not per statement), so passing None matches
        the first entry found for that run_uuid, which is enough. Pass
        a specific identity when a caller genuinely needs one exact
        statement's own entry, not just any entry for the run."""
        for entry in ledger:
            if entry.get("run_uuid") != run_uuid:
                continue
            if identity is not None and entry.get("identity") != identity:
                continue
            return entry
        return None

    @classmethod
    def _read_accessor(cls, instance_dir: str, accessor):
        """resolves a well-known instance-level file accessor (errors/
        vars/meta -> parsed JSON; data/unmatched -> raw bytes, both
        genuinely optional, None if never written; file("...") -> raw
        bytes of the user-named file, also optional). :errors() may
        carry a nested :idchain(...) argument, filtering the parsed
        list down to entries whose own "source" field (Error.to_json()
        -- Matchable.my_chain, recorded once at error time, not walked
        live) matches -- zero matches is a legitimate empty list, not
        None or an error; the file itself was found and read fine."""
        if accessor.name in cls._JSON_ACCESSOR_FILES:
            path = Nos(instance_dir).join(cls._JSON_ACCESSOR_FILES[accessor.name])
            data = cls._read_well_known_json(path)
            if (
                data is not None
                and accessor.name == "errors"
                and isinstance(accessor.arg, Idchain3)
            ):
                data = [e for e in data if accessor.arg.matches(e.get("source"))]
            return data
        if accessor.name in cls._BYTES_ACCESSOR_FILES:
            path = Nos(instance_dir).join(cls._BYTES_ACCESSOR_FILES[accessor.name])
            return cls._read_well_known_file(path)
        path = Nos(instance_dir).join(accessor.arg)
        return cls._read_well_known_file(path)

    def _discover_run_homes(self, root_major: str | None) -> list[tuple[str, str]]:
        """every distinct, still-existing (run_home, named_paths_name)
        pair, read from the archive-root manifest.json -- see this
        module's own docstring for why this replaces directory-walking
        entirely (no need to know/guess a group's template depth).
        root_major is a literal group name to filter to (the ordinary,
        single-group case), or None to skip the filter entirely and
        discover across every group -- used by '*' traversal, which
        already has this same archive-wide ledger in hand for Rule
        1a/1b, so no separate group-name enumeration is needed. Each
        pair's own group name is kept (not just the run_home) so '*'
        traversal can tell whether a given run is a direct child of
        *its own* group's home -- needed once a plain bare pointer
        means zero-level-only (settled 2026-08-10, see :flatten() for
        the any-depth case) rather than "ignore depth entirely." Many
        entries can share the same run_home (one entry per csvpath-
        statement execution, several statements per run), so dedupe; a
        stale entry (the run since deleted) is dropped via an
        existence check."""
        archive = self.csvpaths.config.get(section="results", name="archive")
        manifest_path = Nos(archive).join("manifest.json")
        if not Nos(manifest_path).exists():
            return []
        with DataFileReader(manifest_path) as reader:
            entries = json.load(reader.source)
        homes = []
        seen = set()
        for entry in entries:
            group = entry.get("named_paths_name")
            if root_major is not None and group != root_major:
                continue
            run_home = entry.get("run_home")
            if run_home and run_home not in seen:
                seen.add(run_home)
                homes.append((run_home, group))
        return [pair for pair in homes if Nos(pair[0]).exists()]

    def _results_for_run(
        self,
        run_dir: str,
        identity: str | None,
        match_all: bool,
        range_bounds: tuple | None = None,
        accessor=None,
    ) -> list[ReferenceResult3]:
        if identity is None and not match_all and range_bounds is None:
            uuid = self._read_json_field(
                Nos(run_dir).join("manifest.json"), "run_uuid"
            )
            return [ReferenceResult3(path=run_dir, uuid=uuid)]

        instances = self._list_instance_identities(run_dir)
        if match_all:
            matched = instances
        elif range_bounds is not None:
            # ':from()'/':to()' as a statement-level range -- added
            # 2026-08-13, David: ":from(:index(2)):unmatched() should
            # definitely not work" -- a range is "more than one entity"
            # the same way ':all()' already is, so it gets the same
            # restriction combined with a content accessor. Unlike
            # ':all()'s own BLANKET rejection there, this is count-
            # DEPENDENT (checked per run, since different runs can have
            # different statement counts) -- mirrors query()'s own
            # run-level "more than one candidate" check exactly, rather
            # than introducing a second style of restriction. A range
            # that happens to narrow to exactly one statement in THIS
            # run is fine with an accessor, same as a bare pointer
            # narrowing a run-list to one already is.
            from_call, to_call = range_bounds
            matched = self._apply_range(instances, from_call, to_call)
            if len(matched) > 1 and accessor is not None:
                raise ReferenceException3(
                    "ResultsReferenceFinder3 requires ':from()'/':to()' to "
                    "narrow to exactly one statement to read full well-"
                    "known-file content -- resolving full content always "
                    "touches exactly one entity, same as ':all()'."
                )
        else:
            index = self._find_by_identity(identity, instances)
            matched = [instances[index]] if index is not None else []

        found = []
        for inst in matched:
            inst_dir = Nos(run_dir).join(inst)
            uuid = self._read_json_field(
                Nos(inst_dir).join("manifest.json"), "uuid"
            )
            found.append(ReferenceResult3(path=inst_dir, uuid=uuid))
        return found

    @classmethod
    def _combined_name_one_calls(cls, name_one) -> list:
        """name_one's own effective function chain, used for both
        pointer-detection (query()) and ":manifest()"-detection
        (_extract_data()) -- the bare/function-only shape's path[0] is
        itself part of the chain (mirrors csvpaths); the literal-path
        shape's path segments are never functions (except :name(...),
        which is path-building, not chain content), so only its
        trailing .functions counts there."""
        if cls._is_bare_function_only(name_one):
            return [name_one.path[0], *name_one.functions]
        return list(name_one.functions)

    @staticmethod
    def _is_bare_function_only(name_one) -> bool:
        """true for a name_one with no literal path at all -- its sole
        path "segment" is itself a version-selecting function (e.g.
        :all()/:first()/:last()/:index(n)), mirroring csvpaths' own
        "path[0] is a FunctionCall3" shape. :name("...") is excluded --
        that is path-*building* (a literal name), not a version
        selector, so it stays in the ordinary literal-path shape even
        as the sole segment."""
        return (
            len(name_one.path) == 1
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name != "name"
        )

    @staticmethod
    def _pointer_from_calls(calls: list):
        """at most one pointer function (:first()/:last()/:index(n))
        among the combined chain selects which run -- build_chain()
        already enforces the "at most one" rule; absent means every run
        comes back unreduced."""
        if not calls:
            return None
        built = ReferenceFunctionFactory.build_chain(calls)
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        return pointers[0] if pointers else None

    @staticmethod
    def _range_calls_from_calls(calls: list) -> tuple:
        """(from_call, to_call) -- the built ':from()'/':to()' Function3
        instances among the combined chain, or None for whichever is
        absent. Neither is a POINTER (both ROLE == CONTEXT_SETTER), so
        they never compete with a real pointer for build_chain()'s "at
        most one pointer" rule -- a pointer riding alongside either one
        reduces the SLICE ':from()'/':to()' already narrowed to, same as
        it already does for ':all()'/':groups()'."""
        if not calls:
            return None, None
        built = ReferenceFunctionFactory.build_chain(calls)
        from_call = next((f for f in built if f.name == "from"), None)
        to_call = next((f for f in built if f.name == "to"), None)
        return from_call, to_call

    @classmethod
    def _apply_date_range(
        cls, run_homes: list, from_date: str | None, to_date: str | None
    ) -> list:
        """filters `run_homes` to those whose own arrival date (parsed
        from each directory's own fixed-width timestamp prefix, see
        _run_dir_date) falls within [from_date, to_date], both
        INCLUSIVE -- date-mode ':from()'/':to()', added 2026-08-13.
        Unlike index-mode (_apply_range, a POSITIONAL slice), this is a
        FILTER, not a slice -- comparing run positions would be
        meaningless for a date bound. run_homes is not assumed to
        already be date-sorted (though in practice it always is, via
        _run_dir_sort_key, since this runs after that sort in query())."""
        result = []
        for rh in run_homes:
            d = cls._run_dir_date(rh)
            if from_date is not None and d < from_date:
                continue
            if to_date is not None and d > to_date:
                continue
            result.append(rh)
        return result

    @staticmethod
    def _run_dir_date(run_home: str) -> str:
        """the run's own arrival date ("YYYY-MM-DD"), parsed from its
        directory name's own fixed-width timestamp prefix -- RunHomeMaker
        always writes "%Y-%m-%d_%H-%M-%S[_N]", so the first 10
        characters are always the date, regardless of any "_N"
        disambiguation suffix. ISO date strings sort/compare
        lexicographically in true chronological order, so plain string
        comparison (see _apply_date_range) is correct, not just
        convenient."""
        seg = run_home.rstrip("/").rsplit("/", 1)[-1]
        return seg[:10]

    _ACCESSOR_NAMES = ("errors", "vars", "meta", "data", "unmatched", "file")

    @staticmethod
    def _name_three_selector(
        name_three,
    ) -> tuple[str | None, bool, object, object, tuple]:
        """returns (identity, match_all, accessor, field_call,
        range_bounds) for name_three -- identity is a literal statement-
        identity string to look up (None if match_all/range_bounds, or
        if no selector is present at all); match_all is True for :all()
        (every instance in the run); range_bounds is (from_call, to_call)
        for ':from()'/':to()' (a positional slice of instances -- added
        2026-08-13, David: ":from(:index(2)):unmatched() should
        definitely not work" -- confirmed a range is "more than one
        entity" the same way :all() already is, see query()'s own
        per-run count check for how this is enforced; unlike :all()'s
        blanket rejection there, though, a range's rejection is count-
        DEPENDENT, mirroring the run-level "more than one candidate"
        check this whole file already uses elsewhere -- a range that
        happens to narrow to exactly one instance is fine with an
        accessor, same as a bare pointer narrowing to one run already
        is), None if absent; accessor is the built well-known-file
        Function3 riding alongside the identity/:all()/range selector;
        field_call is a registered field-accessor Function3 (e.g.
        :uuid()) riding there instead -- kept separate from accessor
        rather than one shared variable, since field accessors are
        exempt from the single-entity pooling rule (see query()) and
        content accessors are not; conflating them would risk the same
        "field accessor accidentally restricted like a content
        accessor" bug already hit twice during the #228 merge.
        Resolving with none of identity/match_all/range_bounds present
        gives None -- "no default". An unrecognized function raises via
        build_chain() itself ("Unknown reference function") if it is
        not registered at all, or is rejected here directly if it is
        registered but not meaningful as a name_three function (e.g.
        :manifest())."""
        if name_three is None:
            return None, False, None, None, None

        match_all = False
        accessor = None
        field_call = None
        from_call = None
        to_call = None
        if name_three.functions:
            built = ReferenceFunctionFactory.build_chain(name_three.functions)
            field_call = ResultsReferenceFinder3._find_field_function_call(built)
            for f in built:
                if f.name == "all":
                    match_all = True
                elif f.name == "from":
                    from_call = f
                elif f.name == "to":
                    to_call = f
                elif f.name in ResultsReferenceFinder3._ACCESSOR_NAMES:
                    accessor = f
                elif f is field_call:
                    continue
                else:
                    raise ReferenceException3(
                        f"ResultsReferenceFinder3 does not yet support "
                        f":{f.name}() as a name_three function."
                    )
        range_bounds = (from_call, to_call) if (from_call or to_call) else None

        body = name_three.body
        if isinstance(body, Star3):
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not support a bare '*' as "
                "name_three's body -- use :all() instead."
            )
        if sum([body is not None, match_all, range_bounds is not None]) > 1:
            raise ReferenceException3(
                "ResultsReferenceFinder3 cannot combine a literal "
                "identity, :all(), and ':from()'/':to()' -- each selects "
                "instances a different, contradictory way; use only one."
            )
        if body is None and not match_all and range_bounds is None:
            raise ReferenceException3(
                "ResultsReferenceFinder3 requires name_three to be a "
                "literal statement identity, :all(), or ':from()'/':to()' "
                "to select which instance(s) a well-known-file function "
                "applies to."
            )
        return body, match_all, accessor, field_call, range_bounds

    @classmethod
    def _group_key(cls, run_home: str, home: str, prefix_len: int = 0) -> tuple:
        """group key for ':all()'/':groups()' partitioning -- every
        segment after the first `prefix_len` (the fixed literal/'*'
        prefix, if any) and before the run's own trailing name, as a
        TUPLE -- not just the last segment. Matters for ':groups()'
        specifically (any depth, so the remaining length varies per
        candidate): two runs sharing a common trailing segment under
        DIFFERENT earlier templates (e.g. "beta/x" vs. "gamma/x") must
        never be conflated into one group just because both end in "x".
        For ':all()', every candidate's remaining length is always
        exactly 1 by construction (the pattern already fixes every
        other position), so a 1-tuple here behaves identically to using
        the bare last-segment string -- this is purely a shared
        implementation, not a behavior change for ':all()'. An empty
        tuple (zero additional segments -- a direct/zero-level run,
        only reachable through ':groups()', never ':all()') is itself a
        valid, distinct group, not a special case needing a guard."""
        segments = cls._prefix_segments(run_home, home)
        return tuple(segments[prefix_len:])

    @staticmethod
    def _prefix_segments(run_home: str, home: str) -> "list[str] | None":
        """everything between `home` and the run directory's own name
        (the last path segment), split into segments -- None if
        run_home is not even under `home` at all. Shared by
        _matches_prefix/_matches_prefix_at_least (matching) and
        query()'s ':all()' grouping (extracting the actual value at a
        wildcarded position, once a candidate is already known to
        match)."""
        home = home.rstrip("/")
        if not run_home.startswith(home):
            return None
        rel = run_home[len(home) :].lstrip("/")
        segments = rel.split("/") if rel else []
        return segments[:-1]

    @classmethod
    def _matches_prefix(cls, run_home: str, home: str, pattern: list) -> bool:
        """true if run_home's own prefix matches `pattern` position-by-
        position (Star3 as wildcard), with EXACTLY len(pattern) segments
        -- no more, no fewer. Similar in spirit to
        FilesReferenceFinder3._matches, but the run directory's own name
        is excluded from the comparison first, since (unlike a file's
        file_home) run_home already includes that final, version-
        identifying segment itself."""
        prefix_segments = cls._prefix_segments(run_home, home)
        if prefix_segments is None or len(prefix_segments) != len(pattern):
            return False
        for actual, expected in zip(prefix_segments, pattern):
            if isinstance(expected, Star3):
                continue
            if actual != expected:
                return False
        return True

    @classmethod
    def _matches_prefix_at_least(cls, run_home: str, home: str, pattern: list) -> bool:
        """like _matches_prefix, but matches when run_home's own prefix
        has AT LEAST len(pattern) segments matching `pattern` position-
        by-position, with any number of additional segments (including
        zero) allowed after them before the run's own trailing name --
        the ':flatten()' case (see that function and its own docstring):
        match this literal/wildcard prefix, then anything, at any
        remaining depth, instead of requiring an exact segment count."""
        prefix_segments = cls._prefix_segments(run_home, home)
        if prefix_segments is None or len(prefix_segments) < len(pattern):
            return False
        for actual, expected in zip(prefix_segments, pattern):
            if isinstance(expected, Star3):
                continue
            if actual != expected:
                return False
        return True

    @classmethod
    def _list_instance_identities(cls, run_dir: str) -> list[str]:
        """every csvpath statement's own result subdirectory within a
        run, named by that statement's identity, sorted into real
        DECLARATION order -- "_extra_data" is the one non-instance
        directory a run dir can contain (manifest.json is a file,
        already excluded by dirs_only).

        Fixed 2026-08-13: this used to return raw directory-listing
        order, which is filesystem-implementation-defined, NOT
        declaration order -- a real, latent bug that ':all()' never
        surfaced (it does not care about order) but ':from()'/':to()'
        absolutely does ("the 3rd through last statement" is meaningless
        without real order). Confirmed by tracing csvpaths.py's own
        enumerate(paths)/enumerate(csvpath_objects) through Result/
        ResultRegistrar/ResultMetadata to the actual written JSON key:
        each instance's own manifest.json carries its declaration-order
        position as "instance_index" (an int, stringified into the
        directory name itself for unnamed statements, but always present
        as this field regardless of whether the statement has an
        explicit identity). Sorting by it, rather than trusting listdir
        order, is the fix."""
        names = [
            name
            for name in Nos(run_dir).listdir(dirs_only=True)
            if name != "_extra_data"
        ]

        def _index(name: str) -> int:
            inst_dir = Nos(run_dir).join(name)
            idx = cls._read_json_field(
                Nos(inst_dir).join("manifest.json"), "instance_index"
            )
            return int(idx) if idx is not None else 0

        return sorted(names, key=_index)

    @classmethod
    def _read_json_field(cls, path: str, field: str):
        """reads one field from a small JSON file (a run's or an
        instance's own manifest.json), tolerating absence -- None if the
        file does not exist rather than raising or fabricating a
        default. Built on the shared _read_well_known_json rather than
        reusing ResultFileReader.json_file() -- that helper writes a
        fresh empty JSON file when one is missing, a write side effect a
        read-only reference query must never trigger."""
        data = cls._read_well_known_json(path)
        return data.get(field) if data else None
