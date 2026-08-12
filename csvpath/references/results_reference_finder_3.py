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
#    other use of "*" goes through _query_star_traversal(), which is
#    deliberately the narrowest of the three datatypes' traversals (bare
#    pointer only, no path narrowing/:all()/name_three/:manifest()/field
#    accessors) -- see that method's own docstring for why the wider cases
#    are genuinely harder here, not just unbuilt yet.
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

        identity, match_all, accessor, _ = self._name_three_selector(
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
            results.extend(self._results_for_run(run_dir, identity, match_all))
        return ReferenceResults3(results=results)

    def _query_star_traversal(self, reference: Reference3) -> ReferenceResults3:
        """root_major == "*" -- query across every named-results group,
        not just one. Deliberately the narrowest '*' traversal of the
        three datatypes: only a bare pointer (:first()/:last()/
        :index(n)), no literal/'*' path narrowing, no name_three, no
        ':all()', no :manifest()/a field-accessor function. A bare
        pointer here means the same zero-level-only ("direct children
        of each run's own group's home") restriction the literal-root
        query() case now applies -- settled 2026-08-10, see that
        method's own comments and :flatten() for the any-depth case.
        Two things make the wider cases genuinely harder here, not just
        unbuilt yet (unlike files/csvpaths, where the same shapes were
        straightforward generalizations):

        - RESULTS' own ':all()' already means something different --
          pooling every csvpath-statement instance WITHIN one already-
          selected run, at name_three (see _name_three_selector) -- so
          there is no existing syntactic home for a "group by named-
          results-group" trigger the way files/csvpaths both have via
          a bare ':all()' in name_one. (Grouping by observed template
          value WITHIN one already-literal group, David's three-
          templates example, is a different, narrower thing and is
          handled in the literal-root query() case, not here.)
        - Literal/'*' path narrowing (_matches_prefix) needs a
          candidate's own group's home directory to compute a relative
          match -- a bare run_home string, once pooled from
          _discover_run_homes(), no longer carries which group it came
          from on its own. _discover_run_homes() now keeps each pair's
          group name specifically so the zero-level check above can
          compute the right home per candidate; genuine non-zero path
          narrowing across every group still needs more design work
          than reusing that, and stays out of scope here.

        So this only generalizes _discover_run_homes() (root_major=None
        skips its group filter -- it already reads the same archive-
        wide ledger Rule 1a/1b use, so no separate group-name
        enumeration is needed at all) and reuses _results_for_run()'s
        existing no-name_three case unchanged. One real design
        decision, independent of the zero-level change: chronological
        order across every group cannot use a full-path string sort the
        way one group's own query() case can get away with (different
        groups' run directories live under different prefixes, so a
        full-path sort would sort by group name first, not by
        timestamp) -- _run_dir_sort_key() extracts just the trailing
        directory-name segment, AND handles that segment's own
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
        if not self._is_bare_function_only(name_one):
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not yet support path "
                "narrowing combined with '*' traversal -- only a bare "
                "pointer (:first()/:last()/:index(n)) is supported so "
                "far, e.g. '$*.results.:last()'."
            )
        if reference.name_three is not None:
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not yet support name_three "
                "(an instance selector) combined with '*' traversal."
            )
        calls = self._combined_name_one_calls(name_one)
        built = ReferenceFunctionFactory.build_chain(calls)
        if any(f.name in ("all", "flatten", "manifest") for f in built):
            # ':flatten()' would be a no-op here anyway -- traversal
            # already pools every discovered run at the same (zero)
            # level, unlike the literal-root case's plain bare pointer
            # -- but rejecting it explicitly avoids silently applying
            # the zero-level filter to what should be an any-depth
            # query, rather than quietly doing the wrong thing.
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not yet support ':all()', "
                "':flatten()', or ':manifest()' combined with '*' "
                "traversal -- only a bare pointer (:first()/:last()/"
                ":index(n)) is supported so far."
            )
        if self._find_field_function_call(calls) is not None:
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not yet support a field-"
                "accessor function combined with '*' traversal."
            )
        pointer = self._pointer_from_calls(calls)
        if pointer is None:
            raise ReferenceException3(
                "ResultsReferenceFinder3 requires a pointer (:first()/"
                ":last()/:index(n)) when traversing every named-results "
                "group with '*'."
            )

        # zero-level (direct children of each run's own group's home)
        # only -- same restriction the literal-root query() case now
        # applies to a plain bare pointer, settled 2026-08-10. Each
        # candidate's own group name (kept by _discover_run_homes since
        # this is the traversal case) is needed to compute the right
        # "home" per candidate -- different groups have different homes.
        run_homes = [
            rh
            for rh, group in self._discover_run_homes(None)
            if self._matches_prefix(
                rh, self.csvpaths.results_manager.get_named_results_home(group), []
            )
        ]
        run_homes = sorted(run_homes, key=self._run_dir_sort_key)
        selected = self._apply_pointer(pointer, run_homes)
        if selected is None:
            return ReferenceResults3(results=[])
        return ReferenceResults3(
            results=self._results_for_run(selected, None, False)
        )

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
        if isinstance(reference.root_major, Star3):
            if result.uuid is not None:
                # Rule 1b -- a pointer already reduced the global ledger
                # to one entry in query(); re-derive it by run_uuid
                # (the archive ledgers own locator -- see query()).
                ledger = self.csvpaths.results_manager.results_root_manifest
                return next(
                    (e for e in ledger if e["run_uuid"] == result.uuid), None
                )
            # global-ledger case (Rule 1a) -- query()'s
            # _query_well_known_file() branch already pointed result.path
            # at the archive-root manifest.json itself, not a run
            # directory, so read it directly rather than joining
            # "manifest.json" onto it again (the ordinary, per-group
            # has_manifest branch below does that join, but only
            # because it deals with a run directory, not a file).
            return self._read_well_known_json(result.path)
        name_one_calls = self._combined_name_one_calls(reference.name_one)
        has_manifest = any(
            seg.contains_function_named("manifest")
            for seg in name_one_calls
            if isinstance(seg, FunctionCall3)
        )
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
            return self._extract_field_value(entry, key_path)

        kind = reference.resolve_kind
        if kind in (Reference3.METADATA_FILE, Reference3.METADATA_FIELD):
            # both land here: :errors() alone classifies as METADATA_FILE,
            # :errors(:idchain(...)) classifies as METADATA_FIELD (a
            # nested pointer-like arg -- see Reference3.resolve_kind) --
            # _read_accessor already handles the idchain-filtering
            # internally based on accessor.arg, so both kinds resolve
            # identically from here.
            _, _, accessor, field_call = self._name_three_selector(
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
                return self._extract_field_value(entry, key_path)
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
        self, run_dir: str, identity: str | None, match_all: bool
    ) -> list[ReferenceResult3]:
        if identity is None and not match_all:
            uuid = self._read_json_field(
                Nos(run_dir).join("manifest.json"), "run_uuid"
            )
            return [ReferenceResult3(path=run_dir, uuid=uuid)]

        instances = self._list_instance_identities(run_dir)
        if match_all:
            matched = instances
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

    _ACCESSOR_NAMES = ("errors", "vars", "meta", "data", "unmatched", "file")

    @staticmethod
    def _name_three_selector(name_three) -> tuple[str | None, bool, object, object]:
        """returns (identity, match_all, accessor, field_call) for
        name_three -- identity is a literal statement-identity string to
        look up (None if match_all, or if no identity/:all() selector is
        present at all); match_all is True for :all() (every instance in
        the run); accessor is the built well-known-file Function3 riding
        alongside the identity/:all() selector; field_call is a
        registered field-accessor Function3 (e.g. :uuid()) riding there
        instead -- kept separate from accessor rather than one shared
        variable, since field accessors are exempt from the single-
        entity pooling rule (see query()) and content accessors are not;
        conflating them would risk the same "field accessor accidentally
        restricted like a content accessor" bug already hit twice during
        the #228 merge. Resolving with neither present gives None -- "no
        default". An unrecognized function raises via build_chain()
        itself ("Unknown reference function") if it is not registered at
        all, or is rejected here directly if it is registered but not
        meaningful as a name_three function (e.g. :manifest())."""
        if name_three is None:
            return None, False, None, None

        match_all = False
        accessor = None
        field_call = None
        if name_three.functions:
            built = ReferenceFunctionFactory.build_chain(name_three.functions)
            field_call = ResultsReferenceFinder3._find_field_function_call(built)
            for f in built:
                if f.name == "all":
                    match_all = True
                elif f.name in ResultsReferenceFinder3._ACCESSOR_NAMES:
                    accessor = f
                elif f is field_call:
                    continue
                else:
                    raise ReferenceException3(
                        f"ResultsReferenceFinder3 does not yet support "
                        f":{f.name}() as a name_three function."
                    )

        body = name_three.body
        if isinstance(body, Star3):
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not support a bare '*' as "
                "name_three's body -- use :all() instead."
            )
        if body is not None and match_all:
            raise ReferenceException3(
                "ResultsReferenceFinder3 cannot combine a literal "
                "identity with :all() -- they select instances two "
                "different, contradictory ways."
            )
        if body is None and not match_all:
            raise ReferenceException3(
                "ResultsReferenceFinder3 requires name_three to be a "
                "literal statement identity or :all() to select which "
                "instance(s) a well-known-file function applies to."
            )
        return body, match_all, accessor, field_call

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

    @staticmethod
    def _list_instance_identities(run_dir: str) -> list[str]:
        """every csvpath statement's own result subdirectory within a
        run, named by that statement's identity -- "_extra_data" is the
        one non-instance directory a run dir can contain (manifest.json
        is a file, already excluded by dirs_only)."""
        return [
            name
            for name in Nos(run_dir).listdir(dirs_only=True)
            if name != "_extra_data"
        ]

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
