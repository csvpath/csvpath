import re
from datetime import datetime

from csvpath.util.nos import Nos
from csvpath.util.original_file_utility import OriginalFileUtility as orut
from csvpath.util.path_util import PathUtility as pathu

from .functions.function_3 import Function3
from .functions.filters.count_3 import Count3
from .functions.filters.idchain_3 import Idchain3
from .functions.filters.message_3 import Message3
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
                # Rule 1b -- a pointer riding beside the bare :manifest()
                # (e.g. "$*.results.:manifest():last()") selects one run
                # record out of the logical manifest set by its position
                # (compendium 6.13b). Until 2026-10-31 it selected a
                # ledger ENTRY, one per instance, so ":index(1)" gave the
                # first run's second instance, not the second run.
                return self._manifest_set_query(pointer=pointer_call)
            return self._query_star_traversal(reference)

        if isinstance(root_major, FunctionCall3):
            # :regex()/:choice() at root_major -- :regex() added
            # 2026-08-27, :choice() added 2026-10-20 (ChoiceSelector3's
            # own .pattern property already compiles down to an
            # equivalent anchored regex alternation, so it is built and
            # used identically from here on). Structurally identical to
            # the Star3 case just above (every group is a candidate),
            # just pre-filtered by pattern before
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
        # moved earlier (not-yet-supported sweep #7 follow-up, 2026-10-21,
        # David: "isn't :groups() being different from :flatten() the
        # whole point?") -- detection only, no application yet (that
        # still happens below, via _narrow()) -- needed this early so
        # group_key_for (just below) can tell whether a range/bare time-
        # window, not just a pointer, will need a per-group reduction.
        from_call, to_call = self._range_calls_from_calls(calls)
        has_range = from_call is not None or to_call is not None
        from_bound = to_bound = None
        from_is_date = to_is_date = False
        if has_range:
            from_bound = self._range_bound(from_call) if from_call is not None else None
            to_bound = self._range_bound(to_call) if to_call is not None else None
            from_is_date = isinstance(from_bound, (str, TimeWindowFunction3))
            to_is_date = isinstance(to_bound, (str, TimeWindowFunction3))
            if (from_bound is not None and to_bound is not None) and (
                from_is_date != to_is_date
            ):
                raise ReferenceException3(
                    "ResultsReferenceFinder3 does not support mixing index-"
                    "mode and date-mode range bounds in the same range."
                )
            if isinstance(from_bound, str):
                self._validate_date_format(from_bound)
            if isinstance(to_bound, str):
                self._validate_date_format(to_bound)
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
        if bare_time_window is not None and has_range:
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not support combining a "
                "bare time-component function (e.g. ':yesterday()') with "
                "an explicit ':from()'/':to()'/':before()'/':after()' "
                "bound in the same name_one chain -- the bare function "
                "already means its own whole period, both ends included."
            )

        def _narrow(cands: list) -> list:
            # applies the range/time-window narrowing -- called once on
            # the whole pooled candidate list in POOL mode, and once per
            # distinct group's own candidate list in GROUP mode (see the
            # two call sites below). Built 2026-10-21: GROUP mode's own
            # defining feature, already established for a plain pointer
            # (reduce independently within each distinct group), applies
            # here too -- a range is just a multi-valued pointer, the
            # same category of terminal reduction, so it follows the
            # identical convention rather than a pooled-then-sliced one.
            if bare_time_window is not None:
                return self._apply_bare_time_window(cands, bare_time_window)
            if has_range:
                if from_is_date or to_is_date:
                    return self._apply_date_range(cands, from_call, to_call)
                return self._apply_range(cands, from_call, to_call)
            return cands

        # group_key_for: set when ':all()'/':groups()' partitions
        # candidates by observed value AND a pointer OR a range/bare
        # time-window exists to reduce each partition (David's three-
        # templates example -- three different one-level templates all
        # group correctly by whatever directory each run actually landed
        # in, not by which template produced it -- ':groups()' extends
        # this to any depth, see _group_key). Left None when none of
        # those is present -- grouping only matters at the reduce step,
        # so with nothing to reduce the "grouped" and "pooled" candidate
        # sets are identical anyway. Widened from "pointer only" to also
        # include range/bare-time-window 2026-10-21 -- same reasoning as
        # _narrow()'s own docstring just above.
        group_key_for = None
        reduces = pointer is not None or has_range or bare_time_window is not None

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
                if reduces:
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
                if reduces:
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
            if reduces:
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
            if reduces:
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
            if reduces:
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
        name_one_field_calls = self._find_field_function_calls(
            self._build_chain(calls), Reference3.RESULTS
        )
        for name_one_field_call in name_one_field_calls:
            # every argued field accessor is its own GATE, wherever it
            # sits in the chain (compendium 6.1) -- e.g.
            # ":error_count(:above(3))". Same literal-root equivalent as
            # _star_pool_and_reduce()'s/_star_group_and_reduce()'s own
            # copy of this filter, see their shared comment for the
            # full reasoning. Was first-match only until 2026-10-30, so
            # ":last():run_uuid():status(\"failed\")" never filtered. A
            # field accessor with no argument is an ordinary field read
            # (e.g. ":uuid()"), not a gate, and is skipped.
            if name_one_field_call.arg is None:
                continue
            candidates = [
                rh
                for rh in candidates
                if self._matches_field_predicate(
                    self._run_field_value(rh, name_one_field_call),
                    name_one_field_call.arg,
                )
            ]

        # range/bare-time-window detection+validation already happened
        # earlier (right after `pointer`/`is_grouped`, so group_key_for
        # could account for it) -- only the actual narrowing (via
        # _narrow(), also defined there) still happens here, applied
        # per-group or pooled below, same position this used to apply
        # it pooled-only, before task #7's follow-up fix made it
        # per-partition.

        (
            identity,
            match_all,
            accessor,
            _,
            range_bounds,
            _,
            instance_pointer,
        ) = self._name_three_selector(reference.name_three)
        has_manifest = any(
            seg.contains_function_named("manifest")
            for seg in calls
            if isinstance(seg, FunctionCall3)
        )
        wants_full_content = has_manifest or accessor is not None
        # partition-aware fix, added 2026-10-20, widened 2026-10-21 (not-
        # yet-supported sweep #7 and its own follow-up): this used to be
        # an unconditional rejection here -- "ResultsReferenceFinder3
        # does not yet support combining ':all()'/':groups()' grouping
        # with :manifest() or a run-level field accessor." group_key_for
        # is only ever set alongside a real reduction step (`reduces` --
        # a pointer and/or a range/bare-time-window, every site that
        # sets it above is itself inside an `if reduces:` guard), so the
        # `if group_key_for:` branch just below already reduces each
        # distinct group to AT MOST one run (via its own pointer, once
        # _narrow() has already windowed that group's own candidates)
        # BEFORE :manifest()/a field accessor ever reads anything -- the
        # identical shape `_star_group_and_reduce()` (this file's own
        # '*'-traversal twin) already proved safe to defer rather than
        # raise, confirmed via its own docstring before porting the fix
        # here. `len(results) > 1` at the bottom can therefore only mean
        # "more than one group's own already-individually-legitimate
        # winner," which `ambiguous_content_read` already defers
        # correctly -- no new exemption needed, this file's own existing
        # computation already handles it.
        if group_key_for:
            # partition candidates by their own observed group key,
            # narrow each partition by the range/time-window (if any),
            # then apply the pointer (if any) independently within each
            # partition -- one result per distinct value observed, or
            # every one of that group's own windowed candidates when
            # there is no pointer to reduce further (David's own worked
            # example, "$*.results.:groups().:from(0):to(1))" --
            # "first 2 runs for each group"). candidates is already
            # sorted by _run_dir_sort_key, so each partition keeps
            # correct arrival order internally.
            groups: dict = {}
            for rh in candidates:
                groups.setdefault(group_key_for[rh], []).append(rh)
            selected_runs = []
            for key in sorted(groups):
                group_candidates = _narrow(groups[key])
                if pointer is not None:
                    selected = self._apply_pointer(pointer, group_candidates)
                    if selected is not None:
                        selected_runs.append(selected)
                else:
                    selected_runs.extend(group_candidates)
        else:
            candidates = _narrow(candidates)
            if pointer is not None:
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
                    run_dir,
                    identity,
                    match_all,
                    range_bounds,
                    accessor,
                    instance_pointer,
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
        set_chain = self._manifest_set_chain(reference)
        if set_chain is not None:
            # the logical manifest set (compendium 6.13b), checked before
            # the run-dir name_three rules below, which do not apply to
            # it: a set name_three may hold :manifest(), and :all() with
            # a content accessor lists every file on query (6.9).
            return self._query_manifest_set(
                reference=reference, chain=set_chain, name_filter=name_filter
            )
        (
            identity,
            match_all,
            accessor,
            _,
            range_bounds,
            _,
            instance_pointer,
        ) = self._name_three_selector(reference.name_three)
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
            (
                pointer,
                all_call,
                flatten_call,
                having_call,
                field_calls,
                groups_call,
                bare_time_window,
                lower_call,
                upper_call,
            ) = self._star_run_selector_chain(calls)
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
                    field_calls,
                    bare_time_window,
                    instance_pointer=instance_pointer,
                    lower_call=lower_call,
                    upper_call=upper_call,
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
                    field_calls,
                    bare_time_window,
                    instance_pointer=instance_pointer,
                    lower_call=lower_call,
                    upper_call=upper_call,
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
                field_calls,
                bare_time_window,
                instance_pointer=instance_pointer,
                lower_call=lower_call,
                upper_call=upper_call,
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
            pointer, _, _, having_call, field_calls, _, bare_time_window, lower_call, upper_call = (
                self._star_run_selector_chain(calls)
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
                field_calls,
                bare_time_window,
                instance_pointer=instance_pointer,
                lower_call=lower_call,
                upper_call=upper_call,
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
            pointer, _, _, having_call, field_calls, _, bare_time_window, lower_call, upper_call = (
                self._star_run_selector_chain(calls)
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
                field_calls,
                bare_time_window,
                instance_pointer=instance_pointer,
                lower_call=lower_call,
                upper_call=upper_call,
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
            pointer, _, _, having_call, field_calls, _, bare_time_window, lower_call, upper_call = (
                self._star_run_selector_chain(calls)
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
                field_calls,
                bare_time_window,
                instance_pointer=instance_pointer,
                lower_call=lower_call,
                upper_call=upper_call,
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
        pointer, _, _, having_call, field_calls, _, bare_time_window, lower_call, upper_call = (
            self._star_run_selector_chain(calls)
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
            field_calls,
            bare_time_window,
            instance_pointer=instance_pointer,
            lower_call=lower_call,
            upper_call=upper_call,
        )

    def _star_run_selector_chain(self, calls: list) -> tuple:
        """validates a run-selecting combined function chain for '*'
        traversal, shared by every _query_star_traversal shape (bare
        and literal/'*'-prefixed alike) -- added 2026-08-19, factored
        out of what used to be inline-only-for-the-bare-case logic once
        the literal/'*'-prefixed shapes needed the identical validation.
        Returns (pointer, all_call, flatten_call, having_call,
        field_calls, groups_call, bare_time_window, lower_call,
        upper_call) -- `lower_call`/`upper_call` (added 2026-10-21,
        closing a real gap this method never had at all: ':from()'/
        ':to()' used to fall straight into the `non_pointers` catch-all
        below, the SAME run-level range query()'s own literal-root path
        already fully supports) are the built ':from()'/':to()' (or
        ':after()'/':before()') calls, validated here exactly the way
        query()'s own literal-root path does (mixing-mode rejection,
        date-format validation) -- the actual application (index-mode
        positional slice vs. date-mode filter, per-partition in GROUP
        mode) happens in _star_pool_and_reduce()/_star_group_and_reduce(),
        which both already receive them. field_calls
        (added 2026-10-18, alongside :error_count()'s own predicate-
        argument GATE) is now a LIST, not a single call: REVISED
        2026-10-18 (compendium 5.20b/GATE-trailing-chain work) once
        ":manifest():uuid(\"...\"):run_home()" and ":manifest():
        named_paths_name(\"...\"):yesterday()" (both confirmed live,
        normative-examples golden-corpus revival) showed a SECOND
        field-accessor chained after the first was rejected outright as
        an unsupported extra -- every argued one in the list is its own
        independent GATE (position does not matter, see
        _star_pool_and_reduce()/_star_group_and_reduce()'s own copies
        of this loop), and _extract_data()'s own resolve-target sites
        separately pick the correct one to resolve to (the LAST, via
        _last_field_function_call() -- see their own comments).
        bare_time_window (added the same day, same fix) is a BARE
        TimeWindowFunction3 (e.g. ":yesterday()") riding in the chain --
        previously silently mismatched for a field_call by accident
        (TimeWindowFunction3.SOURCE == "clock" is "not None" too, so
        _find_field_function_call() used to return it whenever it was
        the only candidate, letting it through the non_pointers
        rejection below while never actually filtering anything, since
        nothing downstream applied it) -- now its own, separate,
        correctly-applied category, mirroring query()'s own already-
        correct literal-root `bare_time_windows` handling (see this
        file's own top-of-method comment there). groups_call added the
        same day as field_call's own original addition, alongside
        ':groups()' finally getting its own '*'-traversal support
        (previously an unconditional rejection -- see this class's own
        comment at the bare-shape dispatch for the worked example that
        needed it).
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
        field_calls = self._find_field_function_calls(built, Reference3.RESULTS)
        bare_time_windows = [f for f in built if isinstance(f, TimeWindowFunction3)]
        if len(bare_time_windows) > 1:
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not support combining more "
                "than one bare time-component function (e.g. "
                "':yesterday()') in the same '*'-traversal chain."
            )
        bare_time_window = bare_time_windows[0] if bare_time_windows else None
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
        # ':from()'/':to()' as a run-level range, now supported during
        # '*' traversal too (built 2026-10-21 -- see this method's own
        # docstring) -- validated here the same way query()'s own
        # literal-root path validates it (mixing-mode rejection, date-
        # format check); the actual application happens in
        # _star_pool_and_reduce()/_star_group_and_reduce().
        lower_call, upper_call = self._range_calls_from_built(built)
        if lower_call is not None or upper_call is not None:
            from_bound = self._range_bound(lower_call) if lower_call is not None else None
            to_bound = self._range_bound(upper_call) if upper_call is not None else None
            from_is_date = isinstance(from_bound, (str, TimeWindowFunction3))
            to_is_date = isinstance(to_bound, (str, TimeWindowFunction3))
            if (from_bound is not None and to_bound is not None) and (
                from_is_date != to_is_date
            ):
                raise ReferenceException3(
                    "ResultsReferenceFinder3 does not support mixing index-"
                    "mode and date-mode range bounds in the same range."
                )
            if isinstance(from_bound, str):
                self._validate_date_format(from_bound)
            if isinstance(to_bound, str):
                self._validate_date_format(to_bound)
            if bare_time_window is not None:
                raise ReferenceException3(
                    "ResultsReferenceFinder3 does not support combining a "
                    "bare time-component function (e.g. ':yesterday()') "
                    "with an explicit ':from()'/':to()'/':before()'/"
                    "':after()' bound in the same '*'-traversal chain -- "
                    "the bare function already means its own whole "
                    "period, both ends included."
                )
        non_pointers = [
            f
            for f in built
            if f.ROLE != Function3.POINTER
            and not any(f is fc for fc in field_calls)
            and f is not bare_time_window
            and f is not flatten_call
            and f is not all_call
            and f is not groups_call
            and f is not manifest_call
            and f is not home_call
            and f is not having_call
            and f is not lower_call
            and f is not upper_call
        ]
        if non_pointers:
            # exhaustive, not partial (not-yet-supported sweep #8) --
            # every other branch in this check already excludes each
            # currently-recognized category by name, so reaching here
            # means a genuinely unrecognized function, not a known one
            # awaiting its own future category.
            raise ReferenceException3(
                f"ResultsReferenceFinder3 does not support "
                f":{non_pointers[0].name}() combined with '*' traversal -- "
                "only a bare pointer (:first()/:last()/:index(n)), "
                "optionally combined with ':all()'/':flatten()'/':groups()', "
                "':manifest()', ':having(\"identity\")', a bare time-"
                "component function (e.g. :yesterday()), ':from()'/':to()', "
                "and/or one or more run-level field-accessor functions "
                "(e.g. :uuid()), is supported."
            )
        pointer = self._pointer_from_calls(calls)
        return (
            pointer,
            all_call,
            flatten_call,
            having_call,
            field_calls,
            groups_call,
            bare_time_window,
            lower_call,
            upper_call,
        )

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
        entry = self.source.run_manifest(run_dir)
        key_path = function_cls.KEY.get(Reference3.RESULTS)
        value = self._extract_field_value(entry, key_path)
        return function_cls.transform_value(value)

    def _any_instance_matches_field(self, run_dir: str, field_call) -> bool:
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
        for identity in self._list_instance_identities(run_dir):
            inst_dir = Nos(run_dir).join(identity)
            entry = self.source.instance_manifest(inst_dir)
            value = self._extract_field_value(entry, key_path)
            value = function_cls.transform_value(value)
            if self._matches_field_predicate(value, field_call.arg):
                return True
        return False

    def _run_satisfies_having(self, run_dir: str, having_call) -> bool:
        """dispatches ':having()'s own three argument shapes -- added
        2026-10-18 alongside its ARG_TYPES widening, shared by every
        call site that used to inline the plain-identity-string check
        directly. A nested Function3 argument (e.g. ':having(:uuid(
        "a381..."))') matches by INSTANCE FIELD value
        (_any_instance_matches_field()); a list (only ever reachable
        via an `@variable` -- the grammar has no literal list syntax)
        matches by ANY of its identity strings being present, added
        same day once a list-valued variable was confirmed live to
        raise instead of working ("does this run/version have an
        instance matching any of these identities," per the normative
        doc's own need); a plain string (the original, unchanged
        shape) matches by ONE instance identity NAME, exactly as
        before."""
        if isinstance(having_call.arg, Function3):
            return self._any_instance_matches_field(run_dir, having_call.arg)
        identities = self._list_instance_identities(run_dir)
        if isinstance(having_call.arg, list):
            return any(identity in identities for identity in having_call.arg)
        return having_call.arg in identities

    def _star_pool_and_reduce(
        self,
        run_homes: list,
        pointer,
        identity: str | None,
        match_all: bool,
        range_bounds: tuple | None,
        accessor,
        having_call=None,
        field_calls: list = None,
        bare_time_window=None,
        instance_pointer=None,
        lower_call=None,
        upper_call=None,
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
        case). `field_calls` (added 2026-10-18, REVISED the same day
        from a single `field_call` to a list -- see
        _star_run_selector_chain()'s own comment) similarly filters
        `run_homes` down to those whose own field value (e.g.
        "error_count") satisfies EACH argued call's own predicate/
        exact-match argument, e.g. ":error_count(:above(3))" -- a no-op
        for any call that carries no argument at all (an ordinary bare
        field read, e.g. ":uuid()", unaffected), and every argued one
        filters independently (AND-combined), regardless of position in
        the chain. `bare_time_window` (added the same day) similarly
        filters `run_homes` to those within its own date range, same as
        query()'s own literal-root `_apply_bare_time_window()` call. A
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
        check at resolve() time means exactly what it says.

        `instance_pointer` (added 2026-10-20, not-yet-supported sweep
        #8) -- a name_three statement-level pointer (issue #418), now
        threaded through to _results_for_run() the same way the
        literal-root query() already does, closing the gap
        _query_star_traversal()'s own docstring used to flag ("nothing
        below this point threads it into _results_for_run()").

        `lower_call`/`upper_call` (added 2026-10-21) -- a run-level
        ':from()'/':to()' range, applied to the pooled `run_homes` list
        the same position `bare_time_window` already occupies (a POOL-
        mode narrowing step, before the pointer reduces further)."""
        if having_call is not None:
            run_homes = [
                rh
                for rh in run_homes
                if self._run_satisfies_having(rh, having_call)
            ]
        for field_call in field_calls or []:
            if field_call.arg is not None:
                run_homes = [
                    rh
                    for rh in run_homes
                    if self._matches_field_predicate(
                        self._run_field_value(rh, field_call), field_call.arg
                    )
                ]
        if bare_time_window is not None:
            run_homes = self._apply_bare_time_window(run_homes, bare_time_window)
        if lower_call is not None or upper_call is not None:
            run_homes = sorted(run_homes, key=self._run_dir_sort_key)
            run_homes = self._apply_run_level_range(run_homes, lower_call, upper_call)
        run_homes = sorted(run_homes, key=self._run_dir_sort_key)
        if pointer is None:
            results = []
            for run_dir in run_homes:
                results.extend(
                    self._results_for_run(
                        run_dir,
                        identity,
                        match_all,
                        range_bounds,
                        accessor,
                        instance_pointer,
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
            selected, identity, match_all, range_bounds, accessor, instance_pointer
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

    #
    # the run-level keys a run record copies from its first ledger entry.
    # every entry of one run carries the same values for these (written
    # once per run by RunRegistrar).
    #
    _RUN_RECORD_KEYS = (
        "run_uuid",
        "run_home",
        "named_paths_name",
        "named_file_name",
        "template",
        "archive_name",
        "archive_path",
        "named_files_root",
        "named_paths_root",
        "lifecycle",
    )

    def _results_ledger_path(self) -> str:
        """the archive ledger's own path, the path every result from the
        logical manifest set carries (compendium 5.5)."""
        archive = self.csvpaths.config.get(section="results", name="archive")
        return Nos(archive).join("manifest.json")

    def _root_name_filter(self, reference: Reference3) -> str | None:
        """the name pattern a :regex()/:choice() root_major filters by,
        or None for '*'."""
        if reference is None:
            raise ValueError("Reference cannot be None")
        if isinstance(reference.root_major, FunctionCall3):
            return self._build(reference.root_major).pattern
        return None

    def _manifest_set_chain(self, reference: Reference3) -> tuple | None:
        """name_one's run selector chain, as _star_run_selector_chain()
        gives it, when `reference` reaches the logical manifest set
        (compendium 6.13b, David 2026-10-31): :manifest() in a function-
        only name_one under '*' or a :regex()/:choice() root, with no
        depth or grouping selector. None otherwise. With one
        (":flatten():manifest()") the reference walks run dirs instead,
        and :manifest() is each selected run's own manifest."""
        if reference is None:
            raise ValueError("Reference cannot be None")
        if not isinstance(reference.root_major, (Star3, FunctionCall3)):
            return None
        if not self._is_bare_function_only(reference.name_one):
            return None
        calls = self._combined_name_one_calls(reference.name_one)
        if not any(f.name == "manifest" for f in self._build_chain(calls)):
            return None
        chain = self._star_run_selector_chain(calls)
        _, all_call, flatten_call, _, _, groups_call, _, _, _ = chain
        if all_call is not None or flatten_call is not None:
            return None
        if groups_call is not None:
            return None
        return chain

    def _query_manifest_set(
        self, *, reference: Reference3, chain: tuple, name_filter: str | None
    ) -> ReferenceResults3:
        """query() for a reference that reaches the logical manifest set.
        `chain` is _manifest_set_chain()'s. A :manifest() with nothing
        else in name_one and no name_three is the whole set: the
        ledger's path, uuid None (5.5). Otherwise run records, or with a
        name_three their instance records, see _manifest_set_query()."""
        if reference is None:
            raise ValueError("Reference cannot be None")
        if chain is None:
            raise ValueError("Chain cannot be None")
        (
            pointer,
            _,
            _,
            having_call,
            field_calls,
            _,
            bare_time_window,
            lower_call,
            upper_call,
        ) = chain
        if reference.name_three is not None and any(
            f.arg is None for f in field_calls
        ):
            # the same rule the run-dir branches apply in _extract_data()
            raise ReferenceException3(
                "ResultsReferenceFinder3 does not support combining a "
                "run-level field accessor on name_one with name_three -- "
                "resolve the run's own field on its own, without a "
                "further instance selector."
            )
        if (
            reference.name_three is None
            and pointer is None
            and having_call is None
            and not field_calls
            and bare_time_window is None
            and lower_call is None
            and upper_call is None
        ):
            ledger_path = self._results_ledger_path()
            return ReferenceResults3(
                results=[ReferenceResult3(path=ledger_path, uuid=None)]
            )
        return self._manifest_set_query(
            pointer=pointer,
            having_call=having_call,
            field_calls=field_calls,
            bare_time_window=bare_time_window,
            lower_call=lower_call,
            upper_call=upper_call,
            name_filter=name_filter,
            name_three=reference.name_three,
        )

    def _manifest_set_runs(self, *, name_filter: str | None) -> list[dict]:
        """the RESULTS logical manifest set's run records (compendium
        6.13b, David 2026-10-31), in arrival order: one record per run,
        at every template depth, deleted runs included. Built from the
        archive ledger, which holds one entry per instance, grouped by
        run_uuid; a run's position is its first instance's arrival.

        A record holds the run-level keys its entries share
        (_RUN_RECORD_KEYS), `time` (its first instance's arrival, which
        is also its ordering key), `manifest_path` (the run's own
        manifest, settled 2026-10-31 -- not the ledger's own path, which
        is what the ledger entries hold) and `instances`, its ledger
        entries in arrival order. Outcome fields (status, valid, error
        counts) are not copied in: a field read gets them from the run
        manifest, see _run_record_field_value(). A field read of :time()
        on a live run therefore reads the run manifest's start, which is
        milliseconds before the record's own `time`; the two are the
        same value under 6.13b(v).

        An entry missing `uuid`, `run_uuid` or `run_home` raises: there
        should be none (David, 2026-10-31, for `uuid`), a run can't be
        grouped without `run_uuid`, and a record can't be placed in time
        or given its manifest without `run_home`. `name_filter` is a
        :regex()/:choice() root's pattern, matched against each run's
        named_paths_name the same way _discover_run_homes() matches it."""
        runs = {}
        for entry in self.source.results_ledger():
            for key in ("uuid", "run_uuid", "run_home"):
                if entry.get(key) is None:
                    msg = f"A results ledger entry has no {key}: {entry}"
                    self.csvpaths.logger.error(msg)
                    raise ValueError(msg)
            name = entry.get("named_paths_name")
            if name_filter is not None and not re.search(name_filter, name or ""):
                continue
            record = runs.get(entry["run_uuid"])
            if record is None:
                record = {key: entry.get(key) for key in self._RUN_RECORD_KEYS}
                record["time"] = entry.get("time")
                record["manifest_path"] = Nos(entry["run_home"]).join("manifest.json")
                record["instances"] = []
                runs[entry["run_uuid"]] = record
            record["instances"].append(entry)
        return list(runs.values())

    def _manifest_set_query(
        self,
        *,
        pointer,
        having_call=None,
        field_calls: list | None = None,
        bare_time_window=None,
        lower_call=None,
        upper_call=None,
        name_filter: str | None = None,
        name_three=None,
    ) -> ReferenceResults3:
        """query() for a :manifest() in name_one that reaches the logical
        manifest set (compendium 6.13b): the run records the reference
        selects, each as the ledger's path plus the run's run_uuid (5.5).
        Filters are ANDed in any order (6.1), the same set of them, with
        the same meanings, _star_pool_and_reduce() applies to run dirs:
        :having() tests a run's instance records, an argued field is a
        filter (6.40), and a time window or range bounds the run's own
        run dir datetime. Ranges and pointers count in arrival order
        (6.13b(ii)), not run dir order. With a `name_three`, the selected
        runs' instance records instead, see
        _manifest_set_instance_results()."""
        records = self._manifest_set_runs(name_filter=name_filter)
        if having_call is not None:
            records = [
                r
                for r in records
                if self._run_record_satisfies_having(record=r, having_call=having_call)
            ]
        for field_call in field_calls or []:
            if field_call.arg is not None:
                records = [
                    r
                    for r in records
                    if self._matches_field_predicate(
                        self._run_record_field_value(record=r, field_call=field_call),
                        field_call.arg,
                    )
                ]
        has_range = lower_call is not None or upper_call is not None
        if bare_time_window is not None or has_range:
            by_home = {r["run_home"]: r for r in records}
            run_homes = [r["run_home"] for r in records]
            if bare_time_window is not None:
                run_homes = self._apply_bare_time_window(run_homes, bare_time_window)
            if has_range:
                run_homes = self._apply_run_level_range(
                    run_homes, lower_call, upper_call
                )
            records = [by_home[rh] for rh in run_homes]
        if pointer is not None:
            selected = self._apply_pointer(pointer, records)
            records = [] if selected is None else [selected]
        if name_three is not None:
            return self._manifest_set_instance_results(
                records=records, name_three=name_three
            )
        ledger_path = self._results_ledger_path()
        return ReferenceResults3(
            results=[
                ReferenceResult3(path=ledger_path, uuid=r["run_uuid"])
                for r in records
            ]
        )

    def _run_record_field_value(self, *, record: dict, field_call):
        """the value a run-level field accessor gives for one run record
        of the logical manifest set. 6.13b(v): the user never chooses the
        source, and where two manifests hold a field the named-entity
        manifest wins for details and outcomes. So the run's own
        manifest is read first; a field it doesn't hold, or a run whose
        manifest is gone (a deleted run), reads the record, by the
        field's LEDGER_KEY if it has one, else its KEY. A deleted run
        therefore has its ledger facts (uuid, home, names, template,
        archive, roots, manifest_path) and None for its outcomes."""
        if record is None or not isinstance(record, dict):
            raise TypeError("Record must be a dict")
        if field_call is None:
            raise ValueError("Field call cannot be None")
        function_cls = ReferenceFunctionFactory.get_registered_class(field_call.name)
        key_path = function_cls.KEY.get(Reference3.RESULTS)
        entry = self.source.run_manifest(record["run_home"])
        value = self._extract_field_value(entry, key_path)
        if value is None:
            record_key = function_cls.LEDGER_KEY.get(Reference3.RESULTS) or key_path
            value = self._extract_field_value(record, record_key)
        return function_cls.transform_value(value)

    def _run_record_satisfies_having(self, *, record: dict, having_call) -> bool:
        """:having() for a run record of the logical manifest set -- the
        same three argument shapes _run_satisfies_having() takes for a
        run dir, tested against the record's instance records rather
        than the run dir's listing, so a deleted run can match too. An
        identity is the ledger entry's own `identity`. A nested field
        (":having(:uuid(\\"...\\"))") reads the instance's own manifest
        first and the ledger entry when that is gone, the same order
        _run_record_field_value() uses one level up."""
        if record is None or not isinstance(record, dict):
            raise TypeError("Record must be a dict")
        if having_call is None:
            raise ValueError("Having call cannot be None")
        arg = having_call.arg
        if isinstance(arg, Function3):
            return self._any_instance_record_matches_field(
                record=record, field_call=arg
            )
        identities = [e.get("identity") for e in record["instances"]]
        if isinstance(arg, list):
            return any(identity in identities for identity in arg)
        return arg in identities

    def _any_instance_record_matches_field(self, *, record: dict, field_call) -> bool:
        """true if any of a run record's instance records has a field
        matching `field_call`'s argument -- the logical-set counterpart of
        _any_instance_matches_field(), which walks a run dir on disk."""
        for entry in record["instances"]:
            value = self._instance_record_field_value(
                record=record, entry=entry, field_call=field_call
            )
            if self._matches_field_predicate(value, field_call.arg):
                return True
        return False

    def _instance_record_field_value(
        self, *, record: dict, entry: dict, field_call
    ):
        """the value an instance-level (name_three) field accessor gives
        for one instance record of the logical manifest set: the
        instance's own manifest first, then its ledger entry, by the
        field's LEDGER_KEY if it has one, else its KEY -- the same order
        _run_record_field_value() uses one level up (6.13b(v)). A
        deleted run's instance therefore has its ledger facts and None
        for its outcomes."""
        if record is None or not isinstance(record, dict):
            raise TypeError("Record must be a dict")
        if entry is None or not isinstance(entry, dict):
            raise TypeError("Entry must be a dict")
        if field_call is None:
            raise ValueError("Field call cannot be None")
        function_cls = ReferenceFunctionFactory.get_registered_class(field_call.name)
        key_path = function_cls.KEY.get(Reference3.RESULT)
        if key_path is None:
            raise ReferenceException3(
                f":{field_call.name}() has no per-instance (name_three) "
                "field to read."
            )
        instance = None
        if entry.get("identity") is not None:
            instance_dir = Nos(record["run_home"]).join(entry["identity"])
            instance = self.source.instance_manifest(instance_dir)
        value = self._extract_field_value(instance, key_path)
        if value is None:
            ledger_key_path = function_cls.LEDGER_KEY.get(Reference3.RESULT) or key_path
            value = self._extract_field_value(entry, ledger_key_path)
        return function_cls.transform_value(value)

    def _manifest_set_instance_selector(self, name_three) -> dict:
        """the parts of a name_three under the logical manifest set
        (compendium 6.13b): how it selects instances (the same identity,
        '*'/:all(), pointer and range rules as a run dir's name_three,
        see _name_three_selector()), its argued fields, which are
        filters (6.40), the unargued field that supplies the value
        (5.20b), and the :manifest() or content accessor that names a
        file. :manifest() and a content accessor together raise: two
        files in one context (6.13b)."""
        if name_three is None:
            raise ValueError("Name three cannot be None")
        (
            identity,
            match_all,
            accessor,
            _,
            range_bounds,
            gate_call,
            pointer,
        ) = self._name_three_selector(name_three, for_manifest_set=True)
        built = self._build_chain(name_three.functions) if name_three.functions else []
        manifest_call = next((f for f in built if f.name == "manifest"), None)
        if manifest_call is not None and accessor is not None:
            raise ReferenceException3(
                f"A name_three :manifest() cannot be combined with "
                f":{accessor.name}() -- each names a different file of "
                "the instance."
            )
        fields = self._find_field_function_calls(built, self.ref.parsed.datatype)
        return {
            "identity": identity,
            "match_all": match_all,
            "pointer": pointer,
            "range_bounds": range_bounds,
            "filters": [f for f in fields if f.arg is not None],
            "value_field": self._last_value_field_call(built),
            "manifest_call": manifest_call,
            "accessor": accessor,
            "gate_call": gate_call,
        }

    def _manifest_set_select_instances(
        self, *, record: dict, selector: dict
    ) -> list[dict]:
        """the instance records of one run record that a name_three
        selects, in arrival order (6.13b(ii)): argued fields filter
        first, then an identity, pointer or range picks, the same way
        filters come before the pointer in name_one."""
        if record is None or not isinstance(record, dict):
            raise TypeError("Record must be a dict")
        if selector is None or not isinstance(selector, dict):
            raise TypeError("Selector must be a dict")
        entries = record["instances"]
        for field_call in selector["filters"]:
            entries = [
                e
                for e in entries
                if self._matches_field_predicate(
                    self._instance_record_field_value(
                        record=record, entry=e, field_call=field_call
                    ),
                    field_call.arg,
                )
            ]
        if selector["pointer"] is not None:
            selected = self._apply_pointer(selector["pointer"], entries)
            return [] if selected is None else [selected]
        if selector["range_bounds"] is not None:
            lower_call, upper_call = selector["range_bounds"]
            return self._apply_range(entries, lower_call, upper_call)
        if selector["identity"] is not None:
            return [e for e in entries if e.get("identity") == selector["identity"]]
        return entries

    def _manifest_set_instance_path(
        self, *, record: dict, entry: dict, selector: dict
    ) -> str:
        """the path query() gives for one selected instance record. A
        reference that names a file gives that file's path (compendium
        6.9, 6.40, 6.41): a name_three :manifest() its manifest.json, a
        content accessor its file. One that names a record or a value
        gives the ledger's path (5.7). A deleted run's file paths are
        still given, since query() always succeeds (5.3); resolve()
        gives None for them."""
        if selector is None or not isinstance(selector, dict):
            raise TypeError("Selector must be a dict")
        if selector["manifest_call"] is None and selector["accessor"] is None:
            return self._results_ledger_path()
        identity = entry.get("identity")
        if identity is None:
            msg = f"A results ledger entry has no identity: {entry}"
            self.csvpaths.logger.error(msg)
            raise ValueError(msg)
        instance_dir = Nos(record["run_home"]).join(identity)
        if selector["manifest_call"] is not None:
            return Nos(instance_dir).join("manifest.json")
        return self._accessor_file_path(
            instance_dir=instance_dir, accessor=selector["accessor"]
        )

    @classmethod
    def _accessor_file_path(cls, *, instance_dir: str, accessor) -> str:
        """the path of the file a content accessor reads in an instance
        dir -- the same names _read_accessor() reads. :original()'s
        extension varies, so it is found by listing the dir; with no such
        file (or no dir) the path is the bare "original" name."""
        if instance_dir is None or instance_dir == "":
            raise ValueError("Instance dir cannot be None or empty")
        if accessor is None:
            raise ValueError("Accessor cannot be None")
        if accessor.name in cls._JSON_ACCESSOR_FILES:
            return Nos(instance_dir).join(cls._JSON_ACCESSOR_FILES[accessor.name])
        if accessor.name == "printouts" and accessor.arg:
            return Nos(instance_dir).join(f"{accessor.arg}.txt")
        if accessor.name == "original":
            nos = Nos(instance_dir)
            if nos.dir_exists():
                for name in nos.listdir(files_only=True):
                    if name.startswith(f"{orut.NAME}.") or name == orut.NAME:
                        return Nos(instance_dir).join(name)
            return Nos(instance_dir).join(orut.NAME)
        if accessor.name in cls._BYTES_ACCESSOR_FILES:
            return Nos(instance_dir).join(cls._BYTES_ACCESSOR_FILES[accessor.name])
        return Nos(instance_dir).join(accessor.arg)

    def _manifest_set_instance_results(
        self, *, records: list, name_three
    ) -> ReferenceResults3:
        """query() for a name_three under the logical manifest set: each
        selected instance record of each selected run, as
        _manifest_set_instance_path()'s path plus the instance's own
        uuid. More than one file selected with no field to supply the
        value is flagged, so resolve() raises: one file's content at a
        time (5.6). A content accessor always reads its file, so it is
        flagged with or without a field, as in the run-dir branches."""
        if records is None:
            raise ValueError("Records cannot be None")
        selector = self._manifest_set_instance_selector(name_three)
        results = []
        for record in records:
            for entry in self._manifest_set_select_instances(
                record=record, selector=selector
            ):
                path = self._manifest_set_instance_path(
                    record=record, entry=entry, selector=selector
                )
                results.append(ReferenceResult3(path=path, uuid=entry["uuid"]))
        reads_a_file = selector["accessor"] is not None or (
            selector["manifest_call"] is not None and selector["value_field"] is None
        )
        return ReferenceResults3(
            results=results, ambiguous_content_read=reads_a_file and len(results) > 1
        )

    def _manifest_set_instance_data(self, *, result: ReferenceResult3, reference):
        """resolve() for one instance record of the logical manifest set,
        found by its uuid. A content accessor gives its file's content
        (and a gate after :errors() applies, as in the run-dir branch);
        else an unargued field gives its value, with or without a
        :manifest() beside it (6.13b); else a :manifest() gives the
        instance's own manifest.json, None if it is gone (a deleted
        run); else the instance record itself, its ledger entry."""
        if result is None:
            raise ValueError("Result cannot be None")
        if reference is None:
            raise ValueError("Reference cannot be None")
        selector = self._manifest_set_instance_selector(reference.name_three)
        runs = self._manifest_set_runs(name_filter=self._root_name_filter(reference))
        found = next(
            (
                (record, entry)
                for record in runs
                for entry in record["instances"]
                if entry["uuid"] == result.uuid
            ),
            None,
        )
        if found is None:
            return None
        record, entry = found
        accessor = selector["accessor"]
        if accessor is not None:
            instance_dir = Nos(record["run_home"]).join(entry["identity"])
            data = self._read_accessor(instance_dir, accessor)
            if selector["gate_call"] is not None:
                return self._apply_errors_gate(data, selector["gate_call"])
            return data
        if selector["value_field"] is not None:
            return self._instance_record_field_value(
                record=record, entry=entry, field_call=selector["value_field"]
            )
        if selector["manifest_call"] is not None:
            instance_dir = Nos(record["run_home"]).join(entry["identity"])
            return self.source.instance_manifest(instance_dir)
        return entry

    def _star_group_and_reduce(
        self,
        partitioned: list,
        pointer,
        identity: str | None,
        match_all: bool,
        range_bounds: tuple | None,
        accessor,
        having_call=None,
        field_calls: list = None,
        bare_time_window=None,
        instance_pointer=None,
        lower_call=None,
        upper_call=None,
    ) -> ReferenceResults3:
        """GROUP mode's shared tail (":all()", bare or literal/'*'-
        prefixed) -- added 2026-08-19. `partitioned`: list of
        (run_home, composite_key) pairs. `having_call` (added
        2026-08-27) filters `partitioned` down to runs containing an
        instance with the given identity, BEFORE partitioning/reducing
        -- same position/reasoning as _star_pool_and_reduce's own copy
        of this filter (not shared as one call, since the two methods
        filter different-shaped inputs -- a flat list here vs. pairs).
        `field_calls`/`bare_time_window` (added 2026-10-18, `field_
        calls` REVISED the same day from a single `field_call` to a
        list) similarly filter `partitioned` down to runs whose own
        field value(s)/run-directory date satisfy them, same reasoning
        as _star_pool_and_reduce's own copy -- see its own comment.
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
        computation applies unchanged in this delegated case). Only
        delegated when there is truly nothing left to reduce by,
        though (added 2026-10-21) -- a run-level ':from()'/':to()'
        range with no pointer still needs its own per-group window
        (David's own worked example, "$*.files.:groups().:from(0):
        to(1))" -- "first 2 registrations for each group"), the same
        reasoning _narrow()'s own docstring explains for query()'s
        literal-root path: GROUP mode's defining feature is reducing
        independently per partition, and a range is just a multi-
        valued pointer, the same category of reduction a plain pointer
        already gets this treatment for."""
        if having_call is not None:
            partitioned = [
                (rh, key)
                for rh, key in partitioned
                if self._run_satisfies_having(rh, having_call)
            ]
        for field_call in field_calls or []:
            if field_call.arg is not None:
                partitioned = [
                    (rh, key)
                    for rh, key in partitioned
                    if self._matches_field_predicate(
                        self._run_field_value(rh, field_call), field_call.arg
                    )
                ]
        if bare_time_window is not None:
            start = bare_time_window.start_datetime()
            end = bare_time_window.end_datetime()
            partitioned = [
                (rh, key)
                for rh, key in partitioned
                if start <= self._run_dir_datetime(rh) <= end
            ]
        has_range = lower_call is not None or upper_call is not None
        if pointer is None and not has_range:
            return self._star_pool_and_reduce(
                [rh for rh, _ in partitioned],
                None,
                identity,
                match_all,
                range_bounds,
                accessor,
                instance_pointer=instance_pointer,
            )
        groups: dict = {}
        for rh, key in partitioned:
            groups.setdefault(key, []).append(rh)
        results = []
        for key in sorted(groups):
            candidates = sorted(groups[key], key=self._run_dir_sort_key)
            if has_range:
                candidates = self._apply_run_level_range(
                    candidates, lower_call, upper_call
                )
            if pointer is not None:
                selected = self._apply_pointer(pointer, candidates)
                selected_runs = [selected] if selected is not None else []
            else:
                selected_runs = candidates
            for rh in selected_runs:
                results.extend(
                    self._results_for_run(
                        rh,
                        identity,
                        match_all,
                        range_bounds,
                        accessor,
                        instance_pointer,
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
        is_set_root = isinstance(reference.root_major, (Star3, FunctionCall3))
        if is_set_root and has_manifest:
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
            if (
                reference.name_three is not None
                and self._manifest_set_chain(reference) is not None
            ):
                # an instance record of the logical manifest set; its
                # path may be a file of the instance, not the ledger
                return self._manifest_set_instance_data(
                    result=result, reference=reference
                )
            if result.path == self._results_ledger_path():
                # the logical manifest set (compendium 6.13b). A uuid
                # is a run record's run_uuid; with none, the result is
                # the whole set, every run record holding its instances
                # -- not the ledger file's own flat list of instances.
                runs = self._manifest_set_runs(
                    name_filter=self._root_name_filter(reference)
                )
                if result.uuid is None:
                    return runs
                record = next(
                    (r for r in runs if r["run_uuid"] == result.uuid), None
                )
                if record is None:
                    return None
                # built, so a bare time window (":today()") is excluded
                # as the filter it is, not taken for a value field
                field_call = self._last_value_field_call(
                    self._build_chain(name_one_calls)
                )
                if field_call is None:
                    return record
                return self._run_record_field_value(
                    record=record, field_call=field_call
                )
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
            entry = self.source.run_manifest(result.path)
            # last-wins (compendium 5.20b, added 2026-10-18) -- was
            # _find_field_function_call() (first match), confirmed wrong
            # the moment a second field accessor could ride alongside
            # :manifest() in the same chain (e.g. the '*'-traversal
            # ":manifest():uuid(...):run_home()" shape -- see
            # _star_run_selector_chain()'s own 2026-10-18 comment).
            # Only an unargued field competes (2026-10-30, see
            # _last_value_field_call()); with none, resolve gives the
            # whole entry, the same as a bare ':manifest()'.
            manifest_field_call = self._last_value_field_call(name_one_calls)
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
                        ledger=self.source.results_ledger(),
                        run_uuid=entry.get("run_uuid") if entry else None,
                    ),
                )
                return function_cls.transform_value(value)
            return entry

        # last-wins (compendium 5.20b, added 2026-10-18) -- same reason
        # as manifest_field_call's own identical change just above.
        # With only argued fields (filters) there is no value to read,
        # so this falls through to "no default" below (compendium 5.21).
        run_field_call = self._last_value_field_call(name_one_calls)
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
            entry = self.source.run_manifest(result.path)
            key_path = function_cls.KEY.get(Reference3.RESULTS)
            value = self._extract_field_value_with_ledger_fallback(
                entry=entry,
                key_path=key_path,
                function_cls=function_cls,
                datatype=Reference3.RESULTS,
                ledger_entry_getter=lambda: self._find_archive_ledger_entry(
                    ledger=self.source.results_ledger(),
                    run_uuid=entry.get("run_uuid") if entry else None,
                ),
            )
            return function_cls.transform_value(value)
        if reference.name_three is None and self._find_field_function_calls(
            name_one_calls, Reference3.RESULTS
        ):
            # every field accessor on name_one is argued -- filters
            # only, already applied on query, so nothing supplies a
            # value: "no default" (compendium 5.21). Without this the
            # METADATA_FIELD kind below raised for a name_three
            # accessor that isn't there (2026-10-30).
            return None

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
            _, _, accessor, field_call, _, gate_call, _ = self._name_three_selector(
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
                entry = self.source.instance_manifest(result.path)
                key_path = function_cls.KEY.get(Reference3.RESULT)
                value = self._extract_field_value_with_ledger_fallback(
                    entry=entry,
                    key_path=key_path,
                    function_cls=function_cls,
                    datatype=Reference3.RESULT,
                    ledger_entry_getter=lambda: self._find_archive_ledger_entry(
                        ledger=self.source.results_ledger(),
                        run_uuid=entry.get("run_uuid") if entry else None,
                        identity=entry.get("instance_identity") if entry else None,
                    ),
                )
                return function_cls.transform_value(value)
        if kind != Reference3.FIRST_PARTY:
            # confirmed unreachable via any real reference (not-yet-
            # supported sweep #10), not a pending gap: by the time
            # name_three.functions reaches resolve_kind's own walk,
            # _name_three_selector() above has already dispatched every
            # one of its members into accessor/field_call/range_bounds/
            # gate_call/pointer_call, or raised its own "does not
            # support :X() as a name_three function" for anything else
            # (confirmed exhaustive in task #8) -- so `kind` can only
            # be METADATA_FILE/METADATA_FIELD here when `accessor` was
            # also set, which the block above already returns from.
            raise ReferenceException3(
                f"ResultsReferenceFinder3 does not support "
                f"resolve_kind={kind!r} -- only :errors()/:vars()/:meta()/"
                ":data()/:unmatched()/:file() are wired up as metadata-"
                "file functions."
            )
        # a run directory (no name_three) or an instance directory matched
        # by identity/:all() with no accessor riding alongside has no
        # single unambiguous payload -- "no default", per "creating
        # references v3.txt"'s resolve table.
        return None

    def _last_value_field_call(self, calls: list) -> "FunctionCall3 | None":
        """the field accessor whose value resolve() returns: the last
        one WITHOUT an argument. An argued field accessor is a filter
        (compendium 6.40; :uuid(\"...\") is a pointer, 6.44) and was
        already applied on query, so it never supplies the value -- a
        filter doesn't return a value (David, 2026-10-29). Only the
        unargued ones compete under 5.20b's last-wins, which is also
        what decides whether its ambiguity warning fires. Every RESULTS
        field argument is a filter: none uses its argument to pick a
        key the way CSVPATHS' ':sources(\"email\")'-style fields do (see
        _apply_key_arg()), so this lives here rather than in the shared
        _last_field_function_call(). Returns None when every field
        accessor in the chain is argued, or there are none."""
        if calls is None:
            raise ValueError("calls cannot be None")
        unargued = [f for f in calls if f.arg is None]
        return self._last_field_function_call(unargued)

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
        return self.source.run_homes(root_major=root_major, name_filter=name_filter)

    def _results_for_run(
        self,
        run_dir: str,
        identity: str | None,
        match_all: bool,
        range_bounds: tuple | None = None,
        accessor=None,
        instance_pointer=None,
    ) -> list[ReferenceResult3]:
        if (
            identity is None
            and not match_all
            and range_bounds is None
            and instance_pointer is None
        ):
            entry = self.source.run_manifest(run_dir)
            uuid = entry.get("run_uuid") if entry else None
            return [ReferenceResult3(path=run_dir, uuid=uuid)]

        instances = self._list_instance_identities(run_dir)
        if match_all:
            matched = instances
        elif instance_pointer is not None:
            # :first()/:last()/:index(n) as a statement-level pointer
            # -- issue #418. Always narrows to at most one, same as
            # every other pointer-consuming shape in this file, via
            # the shared ReferenceFinder3._apply_pointer() -- no
            # "more than one" guard needed the way range_bounds' own
            # branch below has, since a pointer can never match more
            # than one candidate by construction.
            selected = self._apply_pointer(instance_pointer, instances)
            matched = [selected] if selected is not None else []
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
            entry = self.source.instance_manifest(inst_dir)
            uuid = entry.get("uuid") if entry else None
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
        "path[0] is a FunctionCall3" shape. :name("...")/:regex(...)/
        :choice(...) are excluded -- all three are path-*building*
        (matching a template segment, literally, by pattern, or by
        exact-match alternation), not a version selector, so they stay
        in the ordinary literal-path shape even as the sole segment
        (added 2026-09-23 for ':regex()', matching ':name()'s' own
        precedent, and 2026-10-20 for ':choice()' the same way -- e.g.
        "$alpha.results.:regex(\"2026-01-01_\").header_checks:errors()"
        needs to reach _compile_path_pattern(), not be misclassified
        as a version-selector/grouping marker the way ':all()'/
        ':first()' are)."""
        return (
            len(name_one.path) == 1
            and isinstance(name_one.path[0], FunctionCall3)
            and name_one.path[0].name not in ("name", "regex", "choice")
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

    @classmethod
    def _apply_run_level_range(
        cls, run_homes: list, lower_call, upper_call
    ) -> list:
        """picks index-mode (positional slice, via the shared
        ReferenceFinder3._apply_range()) vs. date-mode (filter, via
        this class's own _apply_date_range()) by each bound's own value
        type -- added 2026-10-21, extracted so _star_pool_and_reduce()/
        _star_group_and_reduce() can apply a run-level ':from()'/':to()'
        range during '*' traversal the same way query()'s own literal-
        root path already does (that path's own equivalent dispatch is
        inlined there rather than calling this, since it was written
        first and this was extracted once a second call site needed the
        identical logic)."""
        from_bound = cls._range_bound(lower_call) if lower_call is not None else None
        to_bound = cls._range_bound(upper_call) if upper_call is not None else None
        from_is_date = isinstance(from_bound, (str, TimeWindowFunction3))
        to_is_date = isinstance(to_bound, (str, TimeWindowFunction3))
        if from_is_date or to_is_date:
            return cls._apply_date_range(run_homes, lower_call, upper_call)
        return cls._apply_range(run_homes, lower_call, upper_call)

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
        *,
        for_manifest_set: bool = False,
    ) -> tuple[str | None, bool, object, object, tuple, object, object]:
        """returns (identity, match_all, accessor, field_call,
        range_bounds, gate_call, pointer_call) for name_three -- identity is a literal statement-
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
        with it. pointer_call (added 2026-10-20, issue #418) is a
        :first()/:last()/:index(n) picking exactly ONE statement
        instance within whichever run(s) name_one matched -- a fourth,
        mutually-exclusive alternative to identity/match_all/
        range_bounds (see the "more than one selection mode" check
        below), composable with `accessor`/`field_call`/`gate_call`
        exactly the way identity already is (e.g. ":last():data()").
        Resolving with none of identity/match_all/range_bounds/
        pointer_call present gives None -- "no default". An
        unrecognized function raises via
        build_chain() itself ("Unknown reference function") if it is
        not registered at all, or is rejected here directly if it is
        registered but not meaningful as a name_three function (e.g.
        :manifest()). Instance method (not a staticmethod, since
        2026-08-27), same reason as _pointer_from_calls()'s own
        docstring: self._build_chain() needs this finder's own
        registered variables. `for_manifest_set` lets a :manifest() and
        every field accessor through unreturned, for the logical manifest
        set's name_three (compendium 6.13b), whose caller,
        _manifest_set_instance_selector(), reads them itself; a run dir's
        name_three still rejects :manifest()."""
        if name_three is None:
            return None, False, None, None, None, None, None

        match_all = False
        accessor = None
        field_call = None
        gate_call = None
        from_call = None
        to_call = None
        pointer_call = None
        set_fields = []
        if name_three.functions:
            built = self._build_chain(name_three.functions)
            if for_manifest_set:
                set_fields = self._find_field_function_calls(
                    built, self.ref.parsed.datatype
                )
            # last-wins (compendium 5.20b, added 2026-10-18) -- same
            # reason as manifest_field_call's own identical change in
            # _extract_data(). Instance call (not the class-qualified
            # staticmethod this used to be), since _last_field_function_
            # call() needs self.csvpaths.logger to warn on ambiguity.
            field_call = self._last_field_function_call(built)
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
                elif for_manifest_set and f.name == "manifest":
                    continue
                elif any(f is s for s in set_fields):
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
                elif f.ROLE == Function3.POINTER:
                    # :first()/:last()/:index(n) picking ONE statement
                    # instance within the matched run(s) -- issue #418,
                    # e.g. "$food.results.:flatten().:last():data()".
                    # The compendium's own worked example
                    # ("$alpha.results.:flatten():first().:last():
                    # manifest()") is the same shape. "At most one
                    # pointer" is already enforced generically by
                    # build_chain() (same precedent _pointer_from_calls()'s
                    # own docstring relies on for name_one), so no
                    # second check is needed here.
                    pointer_call = f
                else:
                    # exhaustive, not partial (not-yet-supported sweep
                    # #8) -- every recognized name_three category
                    # (identity/match_all/accessor/field/range/gate/
                    # pointer) is already matched by an earlier branch
                    # in this same dispatch; reaching here means a
                    # genuinely unrecognized function.
                    raise ReferenceException3(
                        f"ResultsReferenceFinder3 does not support "
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
        if (
            sum(
                [
                    body is not None,
                    match_all,
                    range_bounds is not None,
                    pointer_call is not None,
                ]
            )
            > 1
        ):
            raise ReferenceException3(
                "ResultsReferenceFinder3 cannot combine a literal "
                "identity, a pointer (:first()/:last()/:index(n)), "
                ":all(), and ':from()'/':to()' -- each selects instances "
                "a different, contradictory way; use only one."
            )
        if (
            body is None
            and not match_all
            and range_bounds is None
            and pointer_call is None
        ):
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
        return (
            body,
            match_all,
            accessor,
            field_call,
            range_bounds,
            gate_call,
            pointer_call,
        )

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

    def _list_instance_identities(self, run_dir: str) -> list[str]:
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
        names = self.source.instance_dirs(run_dir)

        def _index(name: str) -> int:
            entry = self.source.instance_manifest(Nos(run_dir).join(name))
            idx = entry.get("instance_index") if entry else None
            return int(idx) if idx is not None else 0

        return sorted(names, key=_index)
