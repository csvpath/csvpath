import json
import re
from datetime import datetime

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos
from csvpath.util.original_file_utility import OriginalFileUtility as orut
from csvpath.util.path_util import PathUtility as pathu

from .functions.function_3 import Function3
from .functions.filters.count_3 import Count3
from .functions.filters.idchain_3 import Idchain3
from .functions.filters.message_3 import Message3
from .functions.filters.predicate_function_3 import PredicateFunction3
from .functions.values.time_window_function_3 import TimeWindowFunction3
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
        seg = pathu.parts(run_home)[-1]
        m = cls._RUN_SUFFIX_RE.match(seg)
        if m:
            return (m.group(1), int(m.group(2)))
        return (seg, -1)

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

        if isinstance(root_major, FunctionCall3):
            # :regex() at root_major -- added 2026-08-27. Structurally
            # identical to the Star3 case just above (every group is a
            # candidate), just pre-filtered by pattern before
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
        if name_one.name_two is not None:
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not support the '#worksheet' "
                "marker (name_two) -- it is files-only."
            )
        # compendium 3.9c/3.9d -- added 2026-09-24. Run before anything
        # else touches name_one.path/.functions, so every dispatch
        # branch below sees the already-normalized shape (a literal '*'
        # wherever a non-exempt function implied one) rather than
        # needing its own awareness of this rule. See
        # _apply_implied_star()'s own docstring.
        self._apply_implied_star(name_one)

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
        for f in self._build_chain(calls):
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
                # bare ':all()' occupies the sole name_one position, i.e.
                # the run_dir slot itself -- REVISED 2026-09-21 (was:
                # "exactly one level, wildcarded", settled 2026-08-11).
                # Per compendium 4.2b, ':all()' degenerates to '*'
                # whenever it sits at the run_dir position, regardless of
                # template depth, because run_dir names never repeat --
                # there is nothing for it to group by. Matching zero-
                # level (pattern=[]), same as a bare pointer alone,
                # rather than requiring one wildcarded level beyond it.
                # The grouping machinery below is left in place rather
                # than skipped: with prefix_len=0, every zero-level run's
                # own _group_key() is the same empty tuple, so they
                # naturally collapse into one group -- degenerate
                # behavior falls out of the existing mechanism instead of
                # needing a special case.
                pattern = []
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
            # segment, e.g. "beta/:all():last()" -- REVISED 2026-09-21
            # (was: "matches exactly one level beyond the prefix,
            # grouped by the value there"). ':all()' here still sits at
            # the run_dir slot -- the prefix before it is fixed/literal,
            # but the position ':all()' itself occupies is still the
            # run's own trailing name, which never repeats (compendium
            # 4.2b). So this degenerates the same way the bare case
            # above does: matches exactly the fixed prefix (same
            # candidate set "beta/*" already gives), and prefix_len
            # equals the prefix's own length (not one more) so every
            # candidate's _group_key() comes back as the same empty
            # tuple -- one group, not one per run.
            if name_one.path[-1].arg is not None:
                raise ReferenceException3(
                    "ResultsReferenceFinder3's ':all()' does not take an "
                    "argument."
                )
            pattern = self._compile_path_pattern(name_one.path[:-1])
            candidates = [
                rh for rh in run_homes if self._matches_prefix(rh, home, pattern)
            ]
            if pointer is not None:
                group_key_for = {
                    rh: self._group_key(rh, home, prefix_len=len(pattern))
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
        elif any(
            isinstance(seg, FunctionCall3) and seg.name == "all"
            for seg in name_one.path[:-1]
        ):
            # a MIDDLE-position ':all()' -- e.g. "test/:all()/one:last()"
            # (added 2026-09-22, closing the deferred-work bucket list
            # gap of the same name). Genuinely different from the
            # "':all()' as the last segment" branch above: there, ':all()'
            # sits at the run_dir slot itself, which never repeats, so it
            # degenerates to '*' (compendium 4.2b). Here it groups by a
            # real, fixed-position template segment, with more required
            # structure (a literal/wildcard suffix) between it and the
            # implied run_dir -- compendium 4.2's own rule: "groups the
            # remaining name_one search space by the names found at the
            # grouping segment." Only ':all()' gets this treatment, not
            # ':groups()'/':flatten()' -- both are any-depth already
            # (their own "last segment" branches above already match any
            # remaining depth after their fixed prefix), so a MIDDLE
            # position for either would be ambiguous about how much of
            # the remainder is "the group" vs "required structure after
            # it" in a way ':all()' is not (its own remainder is always
            # exactly one segment, by construction).
            all_index = next(
                i
                for i, seg in enumerate(name_one.path)
                if isinstance(seg, FunctionCall3) and seg.name == "all"
            )
            if name_one.path[all_index].arg is not None:
                raise ReferenceException3(
                    "ResultsReferenceFinder3's ':all()' does not take an "
                    "argument."
                )
            prefix_pattern = self._compile_path_pattern(name_one.path[:all_index])
            # _compile_path_pattern() itself rejects a second ':all()'/
            # ':groups()'/':flatten()' in the suffix (none of them are
            # SOURCE == "clock"), enforcing compendium 4.2b's "name_one
            # can have only one :all() or :groups()" for free, no
            # separate check needed here.
            suffix_pattern = self._compile_path_pattern(
                name_one.path[all_index + 1 :]
            )
            pattern = [*prefix_pattern, Star3(), *suffix_pattern]
            candidates = [
                rh for rh in run_homes if self._matches_prefix(rh, home, pattern)
            ]
            if pointer is not None:
                # _group_key()'s own "every segment after prefix_len, as
                # a tuple" already does the right thing here even though
                # the suffix segments are included in that tuple too
                # (e.g. (X, "one") instead of just (X,)) -- the suffix is
                # FIXED by the pattern match itself, identical across
                # every candidate in this set, so grouping by the longer
                # tuple partitions identically to grouping by X alone.
                group_key_for = {
                    rh: self._group_key(rh, home, prefix_len=len(prefix_pattern))
                    for rh in candidates
                }
        else:
            # plain literal/'*' path, no trailing ':flatten()'/':all()'/
            # ':groups()' marker, e.g. "customers/2025" or "beta/*" or
            # bare "*". REVISED 2026-09-21: when the LAST written segment
            # is itself a bare '*' (Star3), it represents the run_dir
            # slot itself, same as the trailing wildcard-like markers
            # above -- dropped before compiling the pattern, since
            # _prefix_segments()/_matches_prefix() already exclude the
            # run's own trailing name from the comparison. A literal
            # last segment (e.g. "2025") is a real, distinct template
            # value and is NOT dropped -- only an explicit trailing '*'
            # gets this treatment. So "beta/*" now matches the same
            # one-level-under-beta candidates "beta/:all():last()" does,
            # and bare "*" alone now matches zero-level, same as a bare
            # pointer.
            path = name_one.path
            if path and isinstance(path[-1], Star3):
                path = path[:-1]
            pattern = self._compile_path_pattern(path)
            candidates = [
                rh for rh in run_homes if self._matches_prefix(rh, home, pattern)
            ]
        candidates = sorted(candidates, key=self._run_dir_sort_key)

        having_call = next(
            (f for f in self._build_chain(calls) if f.name == "having"),
            None,
        )
        if having_call is not None:
            # filters the run pool down to runs that contain an instance
            # (a csvpath statement result) with this identity -- added
            # 2026-08-27, mirroring CsvpathsReferenceFinder3's own
            # ':having()' (manifest-array membership there; a real
            # filesystem listing here, since RESULTS has no equivalent
            # "named_paths_identities" field to read off a run). Applied
            # BEFORE ':from()'/':to()'/the pointer reduce below, same
            # position ':having()' occupies in CSVPATHS' own
            # _resolve_versions(). group_key_for (if set) needs no
            # separate trim -- its own consumer below only ever looks up
            # keys for `rh in candidates`, so extra now-unused entries
            # for filtered-out runs are simply never read.
            candidates = [
                rh
                for rh in candidates
                if self._run_satisfies_having(rh, having_call)
            ]
        name_one_field_call = self._find_field_function_call(
            self._build_chain(calls)
        )
        if name_one_field_call is not None and name_one_field_call.arg is not None:
            # :error_count()'s own predicate-argument GATE (added
            # 2026-10-18, e.g. ":error_count(:above(3))") -- same
            # literal-root equivalent as _star_pool_and_reduce()'s/
            # _star_group_and_reduce()'s own copy of this filter, see
            # their shared comment for the full reasoning. A no-op
            # whenever the field accessor carries no argument at all
            # (an ordinary bare field read, e.g. ":uuid()").
            candidates = [
                rh
                for rh in candidates
                if self._matches_field_predicate(
                    self._run_field_value(rh, name_one_field_call),
                    name_one_field_call.arg,
                )
            ]

        from_call, to_call = self._range_calls_from_calls(calls)
        # Gap 1 of compendium 6.27/TimeWindowFunction3 (added 2026-10-17)
        # -- a BARE time-component function riding in the chain, with
        # no explicit ':from()'/':to()'/':before()'/':after()' of its
        # own (6.27e's first bullet, "use as a range" -- the compendium's
        # own flagship example, "$acme.files.:yesterday()"). Detected as
        # its own, separate entry in `built` -- a TimeWindowFunction3
        # nested as from_call's/to_call's own .arg (Gap 2, already
        # handled below) never shows up here, it is that call's .arg,
        # not a sibling entry in the chain.
        bare_time_windows = [
            f for f in self._build_chain(calls) if isinstance(f, TimeWindowFunction3)
        ]
        if len(bare_time_windows) > 1:
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not support combining more "
                "than one bare time-component function (e.g. "
                "':yesterday()') in the same name_one chain."
            )
        bare_time_window = bare_time_windows[0] if bare_time_windows else None
        if bare_time_window is not None and (
            from_call is not None or to_call is not None
        ):
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not support combining a "
                "bare time-component function (e.g. ':yesterday()') with "
                "an explicit ':from()'/':to()'/':before()'/':after()' "
                "bound in the same name_one chain -- the bare function "
                "already means its own whole period, both ends included."
            )
        if bare_time_window is not None:
            candidates = self._apply_bare_time_window(candidates, bare_time_window)
        elif from_call is not None or to_call is not None:
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
                    "ResultsReferenceFinder3 does not support mixing index-"
                    "mode and date-mode range bounds in the same range."
                )
            if from_is_date or to_is_date:
                # a TimeWindowFunction3 bound has nothing to validate
                # this way -- it is never a raw user-supplied string
                # (Date3 already validates its own format at
                # construction, in check_valid()); only a bare string
                # bound (":from(\"2025-01-01\")") needs this check.
                if isinstance(from_bound, str):
                    self._validate_date_format(from_bound)
                if isinstance(to_bound, str):
                    self._validate_date_format(to_bound)
                candidates = self._apply_date_range(candidates, from_call, to_call)
            else:
                candidates = self._apply_range(candidates, from_call, to_call)

        identity, match_all, accessor, _, range_bounds, _ = self._name_three_selector(
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
            # Resolving full manifest/well-known-file content for more
            # than one run at once is still illegal (Rule 1, manifest_
            # field_functions_proposal.md's "Entity resolution and
            # pooling" section) -- but query() itself is always allowed
            # to return every match, regardless of accessor (moved
            # 2026-08-26, see the ":path()" retirement/Rule 1 bucket-
            # list entry); this flags the result instead of raising, and
            # ReferenceFinder3.resolve_from() raises only if a caller
            # actually tries to resolve more than one of these at once.
            selected_runs = candidates

        # :all() pools every instance in the run -- each instance has its
        # own separate well-known file on disk. Used to be an immediate,
        # unconditional rejection here ("no established case needs
        # ':all()' combined with a content accessor") -- that case has
        # now arrived (":errors(:count(:above(10)))", normative examples
        # 489-491, needs every instance pooled so each one's own count
        # can be gated independently). Relaxed 2026-10-17 to the same
        # deferred Rule 1 pattern _star_pool_and_reduce() already uses
        # for the identical match_all+accessor combination reached via
        # '*'-root traversal -- query() itself never raises for this,
        # only resolve()/resolve_from() do, and only when more than one
        # of the pooled results is actually asked for at once.
        results = []
        for run_dir in selected_runs:
            results.extend(
                self._results_for_run(
                    run_dir, identity, match_all, range_bounds, accessor
                )
            )
        return ReferenceResults3(
            results=results,
            ambiguous_content_read=wants_full_content and len(results) > 1,
        )

    def _query_star_traversal(
        self, reference: Reference3, name_filter: str | None = None
    ) -> ReferenceResults3:
        """root_major == "*" -- query across every named-results group,
        not just one. Mirrors query()'s own dispatch tree (bare
        function-only / prefix+':flatten()' / prefix+':all()' /
        prefix+':groups()' / plain literal-'*' path), just computing
        each candidate's own home per its own group (via
        _discover_run_homes(None), which keeps each pair's group name
        specifically for this) instead of one fixed home -- added
        2026-08-19, closing the "literal/'*' path narrowing" gap this
        method used to reject outright. `name_filter` (added 2026-08-27,
        query()'s own :regex()-at-root_major branch) restricts every
        _discover_run_homes(None) call below to groups whose own name
        matches the pattern -- "every group whose name matches this
        pattern" is the SAME candidate-gathering '*' already does here,
        just pre-filtered before enumeration, not a new traversal mode.
        None (the default) means every group, the ordinary '*' case,
        unchanged. ':groups()' (any-depth GROUP, bare and literal/'*'-
        prefixed alike) is now supported too -- BUILT 2026-10-18, see
        `_star_run_selector_chain()`'s own `groups_call` and this
        method's own dedicated branches, closing the one remaining
        unconditional rejection here (`normative_reference_examples.txt`'s
        own `$*.results.:groups():named_file_name("orders"):first()`).
        name_three (an instance selector) is now supported too (added
        2026-08-19)
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
        identity, match_all, accessor, _, range_bounds, _ = self._name_three_selector(
            reference.name_three
        )
        if match_all and accessor is not None:
            # :all() at name_three means every instance in whichever
            # run(s) match, each with its own separate well-known file
            # on disk. query()'s own literal-root equivalent of this
            # check was relaxed 2026-10-17 (deferred to the
            # ambiguous_content_read/Rule-1 pattern instead, see its own
            # comment) once ":errors(:count(:above(10)))" needed it for
            # a literal root_major -- left as an unconditional rejection
            # HERE deliberately, since no worked example yet needs this
            # combination across a '*'-root traversal specifically; a
            # future one could extend this the same way, but doing so
            # now would also require re-auditing _star_group_and_reduce's
            # own "len(results) > 1 can only mean legitimate multi-group
            # winners" reasoning below, which currently depends on this
            # staying a hard block.
            raise ReferenceException3(
                "ResultsReferenceFinder3 requires a specific statement "
                "identity, not :all(), to read full well-known-file "
                "content -- resolving full content always touches "
                "exactly one entity."
            )

        if self._is_bare_function_only(name_one):
            calls = self._combined_name_one_calls(name_one)
            pointer, all_call, flatten_call, having_call, field_call, groups_call = (
                self._star_run_selector_chain(calls)
            )
            if all_call is not None:
                # zero-level, degenerate -- the SAME [] restriction bare
                # ':all()' already applies for one literal group (see the
                # literal-root query() branch's own 2026-09-21 revision),
                # just computed per candidate's own group home. Every
                # zero-level run's _group_key() comes back as the same
                # empty tuple, so this naturally collapses to one group
                # per named-results group rather than one per run.
                partitioned = []
                for rh, group in self._discover_run_homes(None, name_filter):
                    home = self.csvpaths.results_manager.get_named_results_home(
                        group
                    )
                    if self._matches_prefix(rh, home, []):
                        partitioned.append(
                            (rh, (group, self._group_key(rh, home)))
                        )
                return self._star_group_and_reduce(
                    partitioned,
                    pointer,
                    identity,
                    match_all,
                    range_bounds,
                    accessor,
                    having_call,
                    field_call,
                )
            if groups_call is not None:
                # any depth, every named-results group -- BUILT
                # 2026-10-18 (normative_reference_examples.txt's own
                # "$*.results.:groups():named_file_name(\"orders\"):
                # first()" -- "select the first run for each template
                # for runs having the named-file name orders"), closing
                # the one remaining unconditional rejection this method
                # had. Same any-depth discovery ':flatten()' already
                # uses below (no prefix restriction of its own), but
                # PARTITIONED by each run's own FULL relative path
                # (_group_key, prefix_len=0) instead of pooled -- the
                # direct '*'-traversal extension of the literal-root
                # query()'s own `is_deep_grouped` branch, and this
                # method's own ':groups()'-as-last-segment sibling
                # below (identical candidate-gathering, just with no
                # fixed prefix to match against first).
                partitioned = []
                for rh, group in self._discover_run_homes(None, name_filter):
                    home = self.csvpaths.results_manager.get_named_results_home(
                        group
                    )
                    partitioned.append((rh, (group, self._group_key(rh, home))))
                return self._star_group_and_reduce(
                    partitioned,
                    pointer,
                    identity,
                    match_all,
                    range_bounds,
                    accessor,
                    having_call,
                    field_call,
                )
            if flatten_call is not None:
                # any depth, every group -- _discover_run_homes(None)
                # already discovers across every group with no depth
                # restriction of its own (the zero-level restriction in
                # the else branch below is applied AFTER discovery, by
                # the _matches_prefix filter, not by discovery itself),
                # so no separate any-depth gathering logic is needed
                # here.
                run_homes = [rh for rh, _ in self._discover_run_homes(None, name_filter)]
            else:
                # zero-level (direct children of each run's own group's
                # home) only -- same restriction the literal-root
                # query() case now applies to a plain bare pointer,
                # settled 2026-08-10.
                run_homes = [
                    rh
                    for rh, group in self._discover_run_homes(None, name_filter)
                    if self._matches_prefix(
                        rh,
                        self.csvpaths.results_manager.get_named_results_home(group),
                        [],
                    )
                ]
            return self._star_pool_and_reduce(
                run_homes,
                pointer,
                identity,
                match_all,
                range_bounds,
                accessor,
                having_call,
                field_call,
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
            pointer, _, _, having_call, field_call, _ = self._star_run_selector_chain(
                calls
            )
            run_homes = [
                rh
                for rh, group in self._discover_run_homes(None, name_filter)
                if self._matches_prefix_at_least(
                    rh,
                    self.csvpaths.results_manager.get_named_results_home(group),
                    prefix_pattern,
                )
            ]
            return self._star_pool_and_reduce(
                run_homes,
                pointer,
                identity,
                match_all,
                range_bounds,
                accessor,
                having_call,
                field_call,
            )

        if isinstance(name_one.path[-1], FunctionCall3) and name_one.path[
            -1
        ].name == "all":
            # a literal/wildcard prefix, then ':all()' as the last path
            # segment, e.g. "beta/:all():last()" -- REVISED 2026-09-21,
            # same reasoning as the literal-root query() branch: ':all()'
            # here still sits at the run_dir slot, so this degenerates to
            # the fixed prefix's own candidate set (same as "beta/*"
            # would give), with prefix_len equal to the prefix's own
            # length so every candidate's _group_key() collapses to the
            # same empty tuple -- one group per named-results group, not
            # one per run.
            if name_one.path[-1].arg is not None:
                raise ReferenceException3(
                    "ResultsReferenceFinder3's ':all()' does not take an "
                    "argument."
                )
            pattern = self._compile_path_pattern(name_one.path[:-1])
            calls = list(name_one.functions)
            pointer, _, _, having_call, field_call, _ = self._star_run_selector_chain(
                calls
            )
            partitioned = []
            for rh, group in self._discover_run_homes(None, name_filter):
                home = self.csvpaths.results_manager.get_named_results_home(group)
                if self._matches_prefix(rh, home, pattern):
                    partitioned.append(
                        (
                            rh,
                            (
                                group,
                                self._group_key(
                                    rh, home, prefix_len=len(pattern)
                                ),
                            ),
                        )
                    )
            return self._star_group_and_reduce(
                partitioned,
                pointer,
                identity,
                match_all,
                range_bounds,
                accessor,
                having_call,
                field_call,
            )

        if isinstance(name_one.path[-1], FunctionCall3) and name_one.path[
            -1
        ].name == "groups":
            # a literal/wildcard prefix, then ':groups()' as the last
            # path segment, e.g. "beta/:groups():last()" -- BUILT
            # 2026-10-18, mirroring the literal-root query()'s own
            # identical branch (matches this prefix, relative to each
            # candidate's OWN group home, then anything at any
            # remaining depth, grouped by everything beyond the fixed
            # prefix) and this method's own ':flatten()'-as-last-
            # segment sibling above (identical candidate-gathering,
            # partitioned instead of pooled).
            if name_one.path[-1].arg is not None:
                raise ReferenceException3(
                    "ResultsReferenceFinder3's ':groups()' does not take "
                    "an argument."
                )
            prefix_pattern = self._compile_path_pattern(name_one.path[:-1])
            calls = list(name_one.functions)
            pointer, _, _, having_call, field_call, _ = self._star_run_selector_chain(
                calls
            )
            partitioned = []
            for rh, group in self._discover_run_homes(None, name_filter):
                home = self.csvpaths.results_manager.get_named_results_home(group)
                if self._matches_prefix_at_least(rh, home, prefix_pattern):
                    partitioned.append(
                        (
                            rh,
                            (
                                group,
                                self._group_key(
                                    rh, home, prefix_len=len(prefix_pattern)
                                ),
                            ),
                        )
                    )
            return self._star_group_and_reduce(
                partitioned,
                pointer,
                identity,
                match_all,
                range_bounds,
                accessor,
                having_call,
                field_call,
            )

        # plain literal/'*' path, no trailing ':flatten()'/':all()'/
        # ':groups()' marker -- POOL mode, exact-length match (relative
        # to each candidate's OWN group home), reduced by the pointer.
        # REVISED 2026-09-21: an explicit trailing '*' represents the
        # run_dir slot itself (same reasoning as the literal-root
        # query()'s own else-branch revision) and is dropped before
        # compiling, so e.g. "beta/*" matches one level under "beta" and
        # bare "*" alone matches zero-level.
        path = name_one.path
        if path and isinstance(path[-1], Star3):
            path = path[:-1]
        pattern = self._compile_path_pattern(path)
        calls = list(name_one.functions)
        pointer, _, _, having_call, field_call, _ = self._star_run_selector_chain(
            calls
        )
        run_homes = [
            rh
            for rh, group in self._discover_run_homes(None, name_filter)
            if self._matches_prefix(
                rh, self.csvpaths.results_manager.get_named_results_home(group), pattern
            )
        ]
        return self._star_pool_and_reduce(
            run_homes,
            pointer,
            identity,
            match_all,
            range_bounds,
            accessor,
            having_call,
            field_call,
        )

    def _star_run_selector_chain(self, calls: list) -> tuple:
        """validates a run-selecting combined function chain for '*'
        traversal, shared by every _query_star_traversal shape (bare
        and literal/'*'-prefixed alike) -- added 2026-08-19, factored
        out of what used to be inline-only-for-the-bare-case logic once
        the literal/'*'-prefixed shapes needed the identical validation.
        Returns (pointer, all_call, flatten_call, having_call,
        field_call, groups_call) -- field_call added 2026-10-18,
        alongside :error_count()'s own predicate-argument GATE, so the
        shared tail methods (_star_pool_and_reduce()/_star_group_and_
        reduce()) can apply it to the pooled candidate list;
        groups_call added the same day, alongside ':groups()' finally
        getting its own '*'-traversal support (previously an
        unconditional rejection -- see this class's own comment at the
        bare-shape dispatch for the worked example that needed it).
        all_call/flatten_call/groups_call are only ever non-None for the
        bare shape (calls includes name_one.path[0] itself there) --
        for a prefixed shape, calls is just name_one.functions, and the
        ':all()'/':flatten()'/':groups()' marker lives in
        name_one.path[-1] instead, inspected separately by the caller,
        so it can never appear in `built` here; returning None for
        those callers is correct, not a missed case.
        A run-level field-accessor function (e.g. :uuid(),
        :named_paths_name() -- added 2026-08-18) is exempt from the
        non-pointer rejection below, same as ':all()'/':flatten()' are:
        _results_for_run() already builds each candidate's
        ReferenceResult3 from its own real run directory, independent
        of any group-name context, so resolving a field from it needs
        nothing star-traversal-specific. ':home()' is exempted the same
        way, but explicitly by name (added 2026-08-26, alongside its own
        SOURCE/KEY narrowing to the zero-level placeholder role only --
        see home_3.py) rather than falling out of the field-accessor
        exemption above for free the way it used to when it still
        declared SOURCE == "manifest".

        A run-filtering ':having("identity")' (added 2026-08-27,
        mirroring CsvpathsReferenceFinder3's own star-traversal support)
        is exempt the same way -- filters the candidate run pool down to
        runs containing a matching instance, applied by the shared
        _star_pool_and_reduce()/_star_group_and_reduce() tail methods
        rather than here, since `built` alone (this method only ever
        sees ONE candidate-gathering shape's own combined chain, not the
        full run list to filter) has nothing to filter yet at this point.

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
        built = self._build_chain(calls)
        field_call = self._find_field_function_call(built)
        all_call = next((f for f in built if f.name == "all"), None)
        flatten_call = next((f for f in built if f.name == "flatten"), None)
        groups_call = next((f for f in built if f.name == "groups"), None)
        manifest_call = next((f for f in built if f.name == "manifest"), None)
        home_call = next((f for f in built if f.name == "home"), None)
        having_call = next((f for f in built if f.name == "having"), None)
        if sum([all_call is not None, flatten_call is not None, groups_call is not None]) > 1:
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not support combining "
                "':all()'/':flatten()'/':groups()' -- each is its own "
                "depth/grouping choice, not to be combined with another."
            )
        non_pointers = [
            f
            for f in built
            if f.ROLE != Function3.POINTER
            and f is not field_call
            and f is not flatten_call
            and f is not all_call
            and f is not groups_call
            and f is not manifest_call
            and f is not home_call
            and f is not having_call
        ]
        if non_pointers:
            raise ReferenceException3(
                f"ResultsReferenceFinder3 does not yet support "
                f":{non_pointers[0].name}() combined with '*' traversal -- "
                "only a bare pointer (:first()/:last()/:index(n)), "
                "optionally combined with ':all()'/':flatten()'/':groups()', "
                "':manifest()', ':having(\"identity\")', and/or a run-level "
                "field-accessor function (e.g. :uuid()), is supported so far."
            )
        pointer = self._pointer_from_calls(calls)
        return pointer, all_call, flatten_call, having_call, field_call, groups_call

    @staticmethod
    def _matches_field_predicate(value, arg) -> bool:
        """generic test for a field-accessor's own predicate/exact-
        match argument -- added 2026-10-18 for :error_count()'s own
        GATE (e.g. ":error_count(:above(3))"/":error_count(0))", the
        first field accessor to carry one. A PredicateFunction3 arg
        (":above()"/":below()", both built as dual-role range-bound/
        predicate classes) delegates to its own matches(); a bare leaf
        value (int/str) is an exact-match test instead -- no dedicated
        predicate class needed for ":error_count(0)". Shared by
        _star_pool_and_reduce()/_star_group_and_reduce()'s own '*'-
        traversal gate and query()'s own literal-root equivalent."""
        if isinstance(arg, PredicateFunction3):
            return arg.matches(value)
        return value == arg

    def _run_field_value(self, run_dir: str, field_call):
        """the value a run-level field-accessor function (e.g.
        :error_count()) reads off this one run's own manifest.json --
        added 2026-10-18 alongside _matches_field_predicate(), shared by
        every call site that needs to test a pooled candidate's own
        field value without yet committing to resolving it as this
        reference's final answer. Runs the SAME transform_value() hook
        _extract_data()'s own field-accessor dispatch applies, so a
        future field accessor whose resolved value differs from its raw
        manifest value (the way :has_errors() does) is gated
        consistently with however it actually resolves."""
        function_cls = ReferenceFunctionFactory.get_registered_class(
            field_call.name
        )
        entry = self._read_well_known_json(Nos(run_dir).join("manifest.json"))
        key_path = function_cls.KEY.get(Reference3.RESULTS)
        value = self._extract_field_value(entry, key_path)
        return function_cls.transform_value(value)

    @classmethod
    def _any_instance_matches_field(cls, run_dir: str, field_call) -> bool:
        """true if ANY of `run_dir`'s own instance subdirectories has a
        field (per `field_call`'s own KEY, instance/RESULT scope) that
        matches `field_call`'s own argument -- added 2026-10-18 for
        ':having()'s own broadened argument (David: "scope it more
        broadly," generalizing past the single :uuid() worked example
        that raised it -- normative_reference_examples.txt's own "$*.
        results.:flatten():having(:uuid(\"a381...\")):run_home()", "the
        run dir of a run containing a csvpath instance with a certain
        UUID"). Distinct from _run_field_value() (reads the RUN's own
        manifest.json, Reference3.RESULTS scope) -- this walks every
        one of the run's own INSTANCE directories (_list_instance_
        identities(), the same real filesystem listing ':having()'s
        own plain-identity-string form already uses) and reads EACH
        one's own manifest.json at Reference3.RESULT scope, stopping at
        the first match (":having()" only needs to know whether one
        exists, not which, or how many)."""
        function_cls = ReferenceFunctionFactory.get_registered_class(
            field_call.name
        )
        key_path = function_cls.KEY.get(Reference3.RESULT)
        if key_path is None:
            raise ReferenceException3(
                f":having() cannot match by :{field_call.name}() -- it has "
                "no per-instance (name_three) field to read."
            )
        for identity in cls._list_instance_identities(run_dir):
            inst_dir = Nos(run_dir).join(identity)
            entry = cls._read_well_known_json(Nos(inst_dir).join("manifest.json"))
            value = cls._extract_field_value(entry, key_path)
            value = function_cls.transform_value(value)
            if cls._matches_field_predicate(value, field_call.arg):
                return True
        return False

    @classmethod
    def _run_satisfies_having(cls, run_dir: str, having_call) -> bool:
        """dispatches ':having()'s own two argument shapes -- added
        2026-10-18 alongside its ARG_TYPES widening, shared by every
        call site that used to inline the plain-identity-string check
        directly. A nested Function3 argument (e.g. ':having(:uuid(
        "a381..."))') matches by INSTANCE FIELD value
        (_any_instance_matches_field()); a plain string (the original,
        unchanged shape) matches by instance IDENTITY NAME, exactly as
        before."""
        if isinstance(having_call.arg, Function3):
            return cls._any_instance_matches_field(run_dir, having_call.arg)
        return having_call.arg in cls._list_instance_identities(run_dir)

    def _star_pool_and_reduce(
        self,
        run_homes: list,
        pointer,
        identity: str | None,
        match_all: bool,
        range_bounds: tuple | None,
        accessor,
        having_call=None,
        field_call=None,
    ) -> ReferenceResults3:
        """POOL mode's shared tail -- added 2026-08-19, alongside
        _star_group_and_reduce(), factored out once name_three needed
        threading through every star-traversal shape identically.
        `having_call` (added 2026-08-27) filters `run_homes` down to
        runs containing an instance with the given identity, BEFORE the
        pointer reduces -- applied here, centrally, rather than in each
        of _query_star_traversal's own four candidate-gathering
        branches, since every one of them already funnels into this
        shared tail (or _star_group_and_reduce's, which applies the same
        filter itself before delegating here for its own no-pointer
        case). `field_call` (added 2026-10-18) similarly filters
        `run_homes` down to those whose own field value (e.g.
        "error_count") satisfies field_call's own predicate/exact-match
        argument, e.g. ":error_count(:above(3))" -- a no-op when
        field_call carries no argument at all (an ordinary bare field
        read, e.g. ":uuid()", unaffected). A
        missing pointer (added 2026-08-19, see _star_run_selector_chain()'s
        own comment for why) means every matched run comes back,
        unreduced -- which can now be MORE than one run. Resolving full
        well-known-file content for more than one run at once is still
        illegal (Rule 1) -- moved from an immediate raise here to the
        same ReferenceResults3.ambiguous_content_read deferred-to-
        resolve() pattern the literal-root run-level case already uses
        (2026-08-26/27, see the ":path()" retirement/Rule 1 bucket-list
        entry) -- query() itself is always allowed to return every
        match. Safe to convert here specifically (unlike GROUP mode's
        own equivalent check in _star_group_and_reduce, left untouched):
        when `pointer` is None there is no per-partition reduction at
        all in THIS branch to worry about conflating with -- every
        matched run is genuinely unreduced, so the flag's own count
        check at resolve() time means exactly what it says."""
        if having_call is not None:
            run_homes = [
                rh
                for rh in run_homes
                if self._run_satisfies_having(rh, having_call)
            ]
        if field_call is not None and field_call.arg is not None:
            run_homes = [
                rh
                for rh in run_homes
                if self._matches_field_predicate(
                    self._run_field_value(rh, field_call), field_call.arg
                )
            ]
        run_homes = sorted(run_homes, key=self._run_dir_sort_key)
        if pointer is None:
            results = []
            for run_dir in run_homes:
                results.extend(
                    self._results_for_run(
                        run_dir, identity, match_all, range_bounds, accessor
                    )
                )
            return ReferenceResults3(
                results=results,
                ambiguous_content_read=accessor is not None and len(results) > 1,
            )
        selected = self._apply_pointer(pointer, run_homes)
        if selected is None:
            return ReferenceResults3(results=[])
        results = self._results_for_run(
            selected, identity, match_all, range_bounds, accessor
        )
        return ReferenceResults3(
            results=results,
            # match_all can still pool more than one instance out of this
            # one, already-pointer-selected run -- added 2026-10-17
            # alongside the ':count()' worked example, same reasoning as
            # the no-pointer branch above (previously unreachable, since
            # match_all+accessor was blocked outright before this fix).
            ambiguous_content_read=accessor is not None and len(results) > 1,
        )

    def _star_group_and_reduce(
        self,
        partitioned: list,
        pointer,
        identity: str | None,
        match_all: bool,
        range_bounds: tuple | None,
        accessor,
        having_call=None,
        field_call=None,
    ) -> ReferenceResults3:
        """GROUP mode's shared tail (":all()", bare or literal/'*'-
        prefixed) -- added 2026-08-19. `partitioned`: list of
        (run_home, composite_key) pairs. `having_call` (added
        2026-08-27) filters `partitioned` down to runs containing an
        instance with the given identity, BEFORE partitioning/reducing
        -- same position/reasoning as _star_pool_and_reduce's own copy
        of this filter (not shared as one call, since the two methods
        filter different-shaped inputs -- a flat list here vs. pairs).
        `field_call` (added 2026-10-18) similarly filters `partitioned`
        down to runs whose own field value satisfies field_call's own
        predicate/exact-match argument, same reasoning as
        _star_pool_and_reduce's own copy -- see its own comment.
        Unlike POOL mode, a pointer here can still select MORE than one
        run overall (one per partition) -- so a name_three CONTENT
        accessor (:errors()/:vars()/etc, as opposed to a poolable field
        accessor like :uuid()) can still touch more than one entity's
        content at once, Rule 1 territory.

        Converted to the deferred `ambiguous_content_read` pattern
        2026-09-28 (was: an unconditional raise here) -- re-audited
        against the exact trap the literal-root ':path()'-retirement fix
        already found and fixed once (CSVPATHS' own `:all():last():
        manifest()`, several groups each already reduced to their OWN
        one candidate by the pointer, is legitimate and must NOT raise
        even though the final count is > 1): confirmed here too, each
        partition's own `_apply_pointer()` call already guarantees AT
        MOST one selected run per group, and `_results_for_run()`'s own
        internal guards (checked below) already guarantee AT MOST one
        `ReferenceResult3` per run whenever `accessor is not None` --
        `match_all` combined with an accessor is intercepted earlier by
        this method's own sibling's unconditional instance-level
        rejection (`_query_star_traversal`'s own `match_all and accessor
        is not None` check, deliberately left in place for '*'-root
        traversal specifically -- see its own comment; query()'s
        LITERAL-root equivalent was relaxed 2026-10-17 for
        ":errors(:count(:above(10)))", but that path never reaches
        this method), and a `range_bounds` match of more than one
        statement is independently rejected inside `_results_for_run()`
        itself. So `len(results) > 1` here can only
        ever mean "more than one GROUP's own already-individually-
        legitimate winner," the identical shape already proven safe to
        defer rather than raise -- flagged via `ambiguous_content_read`
        instead, same as every other Rule 1 call site in this file.
        A name_three FIELD accessor (e.g. ".invoices:uuid()") was never
        rejected here to begin with -- confirmed live against the
        already-shipped literal-root precedent (":all():last().invoices
        :uuid()" resolves fine, poolable, one result per matched run)
        before this was first written.

        A missing pointer (added 2026-08-19) means every matched run
        comes back, unreduced -- mirroring CsvpathsReferenceFinder3's
        own already-shipped ':all()'-with-no-pointer precedent
        (extends the filtered manifest, ungrouped) exactly: once there
        is no pointer to reduce a partition to one, the partitioning
        itself stops mattering for the OUTPUT (every member of every
        partition just comes back), so this degenerates to the same
        "list everything, unreduced" case _star_pool_and_reduce()
        already handles -- delegated there directly rather than
        duplicating that logic (that method's own ambiguous_content_read
        computation applies unchanged in this delegated case)."""
        if having_call is not None:
            partitioned = [
                (rh, key)
                for rh, key in partitioned
                if self._run_satisfies_having(rh, having_call)
            ]
        if field_call is not None and field_call.arg is not None:
            partitioned = [
                (rh, key)
                for rh, key in partitioned
                if self._matches_field_predicate(
                    self._run_field_value(rh, field_call), field_call.arg
                )
            ]
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
        return ReferenceResults3(
            results=results,
            ambiguous_content_read=accessor is not None and len(results) > 1,
        )

    _JSON_ACCESSOR_FILES = {
        "errors": "errors.json",
        "vars": "vars.json",
        "meta": "meta.json",
    }
    _BYTES_ACCESSOR_FILES = {
        "data": "data.csv",
        "unmatched": "unmatched.csv",
        "printouts": "printouts.txt",
    }

    def _extract_data(self, result: ReferenceResult3):
        reference = self.ref.parsed
        log_call = self._bare_log_call(reference)
        if log_call is not None:
            return self._read_log_file(result.path, log_call.arg)
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
            entry = self._read_well_known_json(
                Nos(result.path).join("manifest.json")
            )
            manifest_field_call = self._find_field_function_call(name_one_calls)
            if manifest_field_call is not None:
                # ':manifest():named_file_uuid()'-style -- added
                # 2026-08-28, David's own worked example ("get all the
                # most recent acme registration uuids used in runs,"
                # $*.results.:flatten():manifest():named_file_uuid()).
                # Found by tracing, not guessed: this branch used to
                # return the WHOLE manifest.json entry unconditionally
                # the moment ':manifest()' was present anywhere in
                # name_one_calls, even when a field accessor was ALSO
                # chained alongside it -- never checking for one, so the
                # narrowing silently never applied (no error, just the
                # wrong shape of data back). :manifest() is not actually
                # required for a run-level field read at all (see
                # run_field_call's own branch just below, reached
                # whenever :manifest() is ABSENT) -- it is legal but
                # redundant here, the same "already reads the field off
                # the matched entity, :manifest() adds nothing" relationship
                # FILES' own :first():uuid() vs. :first():manifest():uuid()
                # has. Reuses the identical extraction logic run_field_
                # call's own branch below already has, just fed the
                # entry already read above instead of re-reading it.
                function_cls = ReferenceFunctionFactory.get_registered_class(
                    manifest_field_call.name
                )
                key_path = function_cls.KEY.get(Reference3.RESULTS)
                value = self._extract_field_value_with_ledger_fallback(
                    entry=entry,
                    key_path=key_path,
                    function_cls=function_cls,
                    datatype=Reference3.RESULTS,
                    ledger_entry_getter=lambda: self._find_archive_ledger_entry(
                        ledger=self.csvpaths.results_manager.results_root_manifest,
                        run_uuid=entry.get("run_uuid") if entry else None,
                    ),
                )
                return function_cls.transform_value(value)
            return entry

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
            value = self._extract_field_value_with_ledger_fallback(
                entry=entry,
                key_path=key_path,
                function_cls=function_cls,
                datatype=Reference3.RESULTS,
                ledger_entry_getter=lambda: self._find_archive_ledger_entry(
                    ledger=self.csvpaths.results_manager.results_root_manifest,
                    run_uuid=entry.get("run_uuid") if entry else None,
                ),
            )
            return function_cls.transform_value(value)

        kind = reference.resolve_kind
        if kind in (Reference3.METADATA_FILE, Reference3.METADATA_FIELD):
            # both land here: :errors() alone classifies as METADATA_FILE,
            # :errors(:idchain(...)) (nested -- the FILTER position,
            # compendium 4.13/4.14) classifies as METADATA_FIELD (a
            # nested pointer-like arg -- see Reference3.resolve_kind) --
            # _read_accessor already handles the idchain-filtering
            # internally based on accessor.arg, so both kinds resolve
            # identically from here. :errors():idchain(...) (CHAINED,
            # not nested -- the GATE position, added 2026-10-17) ALSO
            # classifies as METADATA_FIELD here (idchain_call is itself
            # a terminal function in the same list, matching
            # resolve_kind's own first-loop check even though it is a
            # sibling rather than a nested arg) -- harmless, since this
            # branch already treats METADATA_FILE/METADATA_FIELD
            # identically and defers the real distinction to accessor/
            # field_call/gate_call below, not to `kind` itself.
            _, _, accessor, field_call, _, gate_call = self._name_three_selector(
                reference.name_three
            )
            if accessor is not None:
                data = self._read_accessor(result.path, accessor)
                if gate_call is not None:
                    # GATE half of "position decides meaning" (David,
                    # 2026-08-21; settled compendium 4.13/4.14) -- a
                    # SEPARATE :idchain(...) chained AFTER :errors() (not
                    # nested as its own argument -- that is the FILTER
                    # half above, pre-existing, untouched) does not
                    # narrow errors.json's own entries; it decides
                    # whether the WHOLE, already-read, UNFILTERED content
                    # is returned at all.
                    return self._apply_errors_gate(data, gate_call)
                return data
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
                value = self._extract_field_value_with_ledger_fallback(
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
                return function_cls.transform_value(value)
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
        None or an error; the file itself was found and read fine. A
        nested :message(...) argument (added 2026-10-17, the direct
        sibling of :idchain(...) -- normative_reference_examples.txt
        places them right next to each other) filters by the entry's
        own "message" field instead, same treatment. A nested
        :count(...) argument (added 2026-10-17, Errors3's own
        documented exception to the nested=FILTER rule) is not a
        per-entry filter at all -- see Count3.matches(), applied here
        directly against `data` (not per-entry) and gating the whole,
        unfiltered list to None if unsatisfied, same all-or-nothing
        treatment _apply_errors_gate() already gives the chained-
        :idchain() GATE case."""
        if accessor.name in cls._JSON_ACCESSOR_FILES:
            path = Nos(instance_dir).join(cls._JSON_ACCESSOR_FILES[accessor.name])
            data = cls._read_well_known_json(path)
            if accessor.name == "errors":
                if isinstance(accessor.arg, Count3):
                    if not accessor.arg.matches(data):
                        data = None
                elif data is not None and isinstance(accessor.arg, Idchain3):
                    data = [e for e in data if accessor.arg.matches(e.get("source"))]
                elif data is not None and isinstance(accessor.arg, Message3):
                    data = [e for e in data if accessor.arg.matches(e.get("message"))]
            return data
        if accessor.name == "printouts" and accessor.arg:
            # a named stream under print-mode:separate (added
            # 2026-09-21) -- "<name>.txt", not the fixed combined-output
            # default. See Printouts3's own docstring for the normative-
            # doc example this matches ("...printouts('greetings')" and
            # "...file('greetings.txt')" are declared equivalent there).
            path = Nos(instance_dir).join(f"{accessor.arg}.txt")
            return cls._read_well_known_file(path)
        if accessor.name == "original":
            # added 2026-10-15 -- unlike every other well-known file
            # here, original.<ext>'s own extension varies by source
            # type, so it cannot be looked up by a fixed name. Mirrors
            # ResultRegistrar._original_file()'s own convention exactly
            # (confirmed against that method before building): list the
            # instance dir, match the "original."-prefixed (or bare
            # "original", extension-less) entry. None if
            # collect_original() was never used here -- same "genuinely
            # optional" treatment as data/unmatched.
            nos = Nos(instance_dir)
            if not nos.dir_exists():
                return None
            for name in nos.listdir(files_only=True):
                if name.startswith(f"{orut.NAME}.") or name == orut.NAME:
                    return cls._read_well_known_file(Nos(instance_dir).join(name))
            return None
        if accessor.name in cls._BYTES_ACCESSOR_FILES:
            path = Nos(instance_dir).join(cls._BYTES_ACCESSOR_FILES[accessor.name])
            return cls._read_well_known_file(path)
        path = Nos(instance_dir).join(accessor.arg)
        return cls._read_well_known_file(path)

    @staticmethod
    def _apply_errors_gate(data, gate_call):
        """GATE half of the position-decides-meaning rule (David,
        2026-08-21; settled compendium 4.13/4.14) -- `gate_call`
        (:idchain(...), chained AFTER :errors() in the same func_chain,
        NOT nested as its own argument -- that is the FILTER half,
        `_read_accessor`'s own `accessor.arg` handling, pre-existing,
        untouched) does not narrow which of `data`'s own entries come
        back; it decides whether `data` -- already read, UNFILTERED --
        is returned AT ALL. Scoped to `:idchain()` only for now (the
        compendium's own settled examples use only `:idchain()` for
        both filter and gate positions, never `:message()`) -- extending
        to `:message()` is a natural follow-up once it exists.
        `data` may be None (errors.json was never written, same
        genuinely-optional treatment every well-known file gets) -- a
        gate has nothing to check in that case, same as a missing file
        for any other accessor. Returns `data` unchanged (the whole,
        unfiltered list) if ANY entry's own "source" field matches the
        gate's predicate, else None -- None, not an empty list, since
        unlike the FILTER's own legitimate "found the file, no entry
        matched" case, a failed gate means there is nothing to resolve
        at all, the same "genuinely optional/absent" treatment every
        other well-known-file miss gets."""
        if data is None:
            return None
        if any(gate_call.matches(e.get("source")) for e in data):
            return data
        return None

    def _discover_run_homes(
        self, root_major: str | None, name_filter: str | None = None
    ) -> list[tuple[str, str]]:
        """every distinct, still-existing (run_home, named_paths_name)
        pair, read from the archive-root manifest.json -- see this
        module's own docstring for why this replaces directory-walking
        entirely (no need to know/guess a group's template depth).
        root_major is a literal group name to filter to (the ordinary,
        single-group case), or None to skip the filter entirely and
        discover across every group -- used by '*' traversal, which
        already has this same archive-wide ledger in hand for Rule
        1a/1b, so no separate group-name enumeration is needed.
        `name_filter` (added 2026-08-27, for :regex() at root_major) is
        an independent, additional filter -- a regex pattern string
        checked against each entry's own group name via re.search(),
        same semantics ReferenceFinder3._segment_matches() already uses
        for Regex3 everywhere else. Always called with root_major=None
        alongside a real name_filter (a literal group name and a
        pattern are mutually exclusive ways to pick which groups are in
        play -- query() never combines them), but kept as two separate
        parameters rather than one, since they mean genuinely different
        things (exact identity vs. pattern match), not just to avoid
        redundant plumbing. Each pair's own group name is kept (not
        just the run_home) so '*' traversal can tell whether a given
        run is a direct child of *its own* group's home -- needed once
        a plain bare pointer means zero-level-only (settled 2026-08-10,
        see :flatten() for the any-depth case) rather than "ignore
        depth entirely." Many entries can share the same run_home (one
        entry per csvpath-statement execution, several statements per
        run), so dedupe; a stale entry (the run since deleted) is
        dropped via an existence check."""
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
            if name_filter is not None and not re.search(name_filter, group or ""):
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
        "path[0] is a FunctionCall3" shape. :name("...")/:regex(...) are
        excluded -- both are path-*building* (matching a template
        segment, literally or by pattern), not a version selector, so
        they stay in the ordinary literal-path shape even as the sole
        segment (added 2026-09-23 for ':regex()', matching ':name()'s'
        own precedent -- e.g. "$alpha.results.:regex(\"2026-01-01_\").
        header_checks:errors()" needs to reach _compile_path_pattern(),
        not be misclassified as a version-selector/grouping marker the
        way ':all()'/':first()' are)."""
        return (
            len(name_one.path) == 1
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name not in ("name", "regex")
        )

    def _pointer_from_calls(self, calls: list):
        """at most one pointer function (:first()/:last()/:index(n))
        among the combined chain selects which run -- build_chain()
        already enforces the "at most one" rule; absent means every run
        comes back unreduced. Instance method (not a staticmethod,
        since 2026-08-27) purely because self._build_chain() now needs
        this finder's own registered variables to resolve any @variable
        argument -- callers already invoke this as self._pointer_from_
        calls(...) everywhere, so nothing else changes."""
        if not calls:
            return None
        built = self._build_chain(calls)
        pointers = [f for f in built if f.ROLE == Function3.POINTER]
        return pointers[0] if pointers else None

    def _range_calls_from_calls(self, calls: list) -> tuple:
        """(lower_call, upper_call) -- the built range-bound Function3
        instances among the combined chain (':from()'/':after()' for
        lower, ':to()'/':before()' for upper, compendium 6.28, see
        ReferenceFinder3._range_calls_from_built()'s own docstring for
        the full generalization reasoning, added 2026-10-16 -- was
        ':from()'/':to()' only before that), or None for whichever is
        absent. None of the four is a POINTER (all ROLE ==
        CONTEXT_SETTER), so they never compete with a real pointer for
        build_chain()'s "at most one pointer" rule -- a pointer riding
        alongside either one reduces the SLICE already narrowed to,
        same as it already does for ':all()'/':groups()'. Instance
        method (not a staticmethod, since 2026-08-27), same reason as
        _pointer_from_calls() above."""
        if not calls:
            return None, None
        built = self._build_chain(calls)
        return self._range_calls_from_built(built)

    @staticmethod
    def _apply_bare_time_window(run_homes: list, call: TimeWindowFunction3) -> list:
        """filters `run_homes` to those whose own arrival datetime
        falls within `call`'s own [start_datetime(), end_datetime()]
        window -- Gap 1 of compendium 6.27/TimeWindowFunction3, added
        2026-10-17: a bare time-component function riding in the chain
        (e.g. ":yesterday()"), with no explicit ':from()'/':to()' of
        its own. Always INCLUSIVE on both ends, unlike the general
        four-way rule _apply_date_range() implements for the explicit,
        directional case -- there is no separate :from()/:to()/
        :before()/:after() here to pick inclusive vs exclusive; the
        bare function always means its own whole period, both ends
        included (compendium 6.27f's own worked example, ":yesterday()"
        used bare: "the first moment of the prior day to the last
        moment of the prior day")."""
        start = call.start_datetime()
        end = call.end_datetime()
        return [
            rh
            for rh in run_homes
            if start <= ResultsReferenceFinder3._run_dir_datetime(rh) <= end
        ]

    @classmethod
    def _apply_date_range(cls, run_homes: list, lower_call, upper_call) -> list:
        """filters `run_homes` to those whose own arrival datetime
        (parsed from each directory's own fixed-width timestamp prefix,
        see _run_dir_datetime) falls within the date range `lower_call`/
        `upper_call` describe -- date-mode ':from()'/':to()' (both
        INCLUSIVE), added 2026-08-13; generalized 2026-10-16 (compendium
        6.28) to also accept their exclusive siblings ':after()'/
        ':before()', mirroring ReferenceFinder3._apply_manifest_date_
        range()'s own generalization. Unlike index-mode (_apply_range, a
        POSITIONAL slice), this is a FILTER, not a slice -- comparing
        run positions would be meaningless for a date bound. run_homes
        is not assumed to already be date-sorted (though in practice it
        always is, via _run_dir_sort_key, since this runs after that
        sort in query()).

        Rewritten 2026-10-17 (compendium 6.27, TimeWindowFunction3) from
        a fixed day-only string-prefix comparison to real datetime
        comparison -- see ReferenceFinder3._apply_manifest_date_range()'s
        own docstring for the full reasoning (identical rewrite, same
        four-way rule, just applied to run directories instead of
        manifest entries); reproduces the exact prior behavior for
        day-granular bounds."""
        lower_start = lower_end = upper_start = upper_end = None
        if lower_call is not None:
            lower_start, lower_end = cls._bound_window(lower_call)
        lower_inclusive = lower_call is None or lower_call.name == "from"
        if upper_call is not None:
            upper_start, upper_end = cls._bound_window(upper_call)
        upper_inclusive = upper_call is None or upper_call.name == "to"
        result = []
        for rh in run_homes:
            d = cls._run_dir_datetime(rh)
            if lower_start is not None:
                if lower_inclusive and d < lower_start:
                    continue
                if not lower_inclusive and d <= lower_end:
                    continue
            if upper_end is not None:
                if upper_inclusive and d > upper_end:
                    continue
                if not upper_inclusive and d >= upper_start:
                    continue
            result.append(rh)
        return result

    @staticmethod
    def _run_dir_datetime(run_home: str) -> datetime:
        """the run's own arrival datetime, parsed from its directory
        name's own fixed-width timestamp prefix -- RunHomeMaker always
        writes "%Y-%m-%d_%H-%M-%S[_N]", so the first 19 characters are
        always a real, parseable datetime, regardless of any "_N"
        disambiguation suffix. Renamed from _run_dir_date() 2026-10-17
        (compendium 6.27, TimeWindowFunction3) -- now parses the full
        datetime (previously only the first 10 characters, the
        "YYYY-MM-DD" date portion) so hour/minute/second-granular
        bounds can compare meaningfully; day-granular bounds still
        compare identically, since truncating a datetime's own date
        portion is exactly what the old string slice did."""
        seg = pathu.parts(run_home)[-1]
        return datetime.strptime(seg[:19], "%Y-%m-%d_%H-%M-%S")

    _ACCESSOR_NAMES = (
        "errors",
        "vars",
        "meta",
        "data",
        "unmatched",
        "printouts",
        "file",
        "original",
    )

    def _name_three_selector(
        self,
        name_three,
    ) -> tuple[str | None, bool, object, object, tuple, object]:
        """returns (identity, match_all, accessor, field_call,
        range_bounds, gate_call) for name_three -- identity is a literal statement-
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
        accessor" bug already hit twice during the #228 merge. gate_call
        is the GATE half of "position decides meaning" (David,
        2026-08-21; settled compendium 4.13/4.14, added 2026-10-17) -- an
        :idchain(...) CHAINED after :errors() in the same func_chain (a
        separate sibling, not nested as :errors()'s own argument -- that
        is the pre-existing FILTER half, untouched) -- requires
        `accessor` to also be present (raises otherwise, below); see
        ResultsReferenceFinder3._apply_errors_gate() for what it does
        with it.
        Resolving with none of identity/match_all/range_bounds present
        gives None -- "no default". An unrecognized function raises via
        build_chain() itself ("Unknown reference function") if it is
        not registered at all, or is rejected here directly if it is
        registered but not meaningful as a name_three function (e.g.
        :manifest()). Instance method (not a staticmethod, since
        2026-08-27), same reason as _pointer_from_calls()'s own
        docstring: self._build_chain() needs this finder's own
        registered variables."""
        if name_three is None:
            return None, False, None, None, None, None

        match_all = False
        accessor = None
        field_call = None
        gate_call = None
        from_call = None
        to_call = None
        if name_three.functions:
            built = self._build_chain(name_three.functions)
            field_call = ResultsReferenceFinder3._find_field_function_call(built)
            # from_call/to_call here mean LOWER/UPPER bound, not
            # literally ":from()'/':to()' -- generalized 2026-10-16
            # (compendium 6.28) to also recognize their exclusive
            # siblings ':after()'/':before()' via the shared
            # _range_calls_from_built(), which also enforces 6.28c's
            # "same direction twice is illegal" rule. Identified by `is`
            # (not `.name`) in the loop below so either alias is
            # transparently skipped past the generic "unrecognized
            # name_three function" rejection, same as before.
            from_call, to_call = self._range_calls_from_built(built)
            for f in built:
                if f.name == "all":
                    match_all = True
                elif f is from_call or f is to_call:
                    continue
                elif f.name in ResultsReferenceFinder3._ACCESSOR_NAMES:
                    accessor = f
                elif f is field_call:
                    continue
                elif isinstance(f, Idchain3):
                    # the GATE shape (e.g. ":errors():idchain(...)") --
                    # added 2026-10-17. Only recognized as a SEPARATE
                    # chain member here, never nested inside another
                    # function's own argument -- a nested
                    # ":errors(:idchain(...))" is the pre-existing
                    # FILTER shape, which never reaches this loop at all
                    # (it is accessor.arg, not its own entry in `built`).
                    gate_call = f
                else:
                    raise ReferenceException3(
                        f"ResultsReferenceFinder3 does not yet support "
                        f":{f.name}() as a name_three function."
                    )
        if gate_call is not None and accessor is None:
            raise ReferenceException3(
                "ResultsReferenceFinder3's ':idchain()' only means "
                "something as a GATE when chained after a content "
                "accessor (e.g. ':errors():idchain(...)') -- it cannot "
                "stand alone in name_three."
            )
        range_bounds = (from_call, to_call) if (from_call or to_call) else None

        body = name_three.body
        if isinstance(body, Star3):
            # compendium 4.2b/4.3a: ":all() devolves to the same
            # meaning as '*' in name_three" -- normative examples
            # 393-404 declare them flatly equivalent (e.g.
            # "$acme.results.:last().:all()" == "$acme.results.
            # :last().*"), so a literal '*' body folds into the same
            # match_all flag ':all()' already sets, rather than being
            # a separate, unsupported shape. Added 2026-10-17 alongside
            # :count()'s own worked example (normative examples
            # 489-491), which needed this to even parse.
            if match_all:
                raise ReferenceException3(
                    "ResultsReferenceFinder3's name_three cannot combine "
                    "a literal '*' body with ':all()' -- both are the "
                    "same wildcard, at most one may be used in "
                    "name_three."
                )
            match_all = True
            body = None
        if sum([body is not None, match_all, range_bounds is not None]) > 1:
            raise ReferenceException3(
                "ResultsReferenceFinder3 cannot combine a literal "
                "identity, :all(), and ':from()'/':to()' -- each selects "
                "instances a different, contradictory way; use only one."
            )
        if body is None and not match_all and range_bounds is None:
            if name_three.functions:
                # compendium 3.19b: "When name_three is solely one or
                # more functions, a '*' is implied, in the same way as
                # in name_one." -- e.g. ":errors(:count(:above(10)))"
                # with nothing else in name_three. Added 2026-10-17,
                # same worked example as the '*'-body carve-out above.
                # By this point an unrecognized function has already
                # raised (above), so `functions` being non-empty here
                # means an accessor/field_call is actually present.
                match_all = True
            else:
                raise ReferenceException3(
                    "ResultsReferenceFinder3 requires name_three to be a "
                    "literal statement identity, :all(), or ':from()'/"
                    "':to()' to select which instance(s) a well-known-"
                    "file function applies to."
                )
        return body, match_all, accessor, field_call, range_bounds, gate_call

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
        home_parts = pathu.parts(home)
        run_parts = pathu.parts(run_home)
        if run_parts[: len(home_parts)] != home_parts:
            return None
        segments = run_parts[len(home_parts) :]
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
            if not cls._segment_matches(expected, actual):
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
            if not cls._segment_matches(expected, actual):
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
