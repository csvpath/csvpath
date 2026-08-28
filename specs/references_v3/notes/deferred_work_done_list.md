# References v3 — Completed Work (formerly on the bucket list)

Companion to `deferred_work_bucket_list.md`. Every entry here started life
on that list and was later built/fixed/resolved — moved here on 2026-08-26
so the bucket list only shows what's actually still outstanding. Kept
verbatim (including its own history/backstory) rather than trimmed to a
one-line changelog, since the reasoning behind *why* something was built
the way it was is often exactly what the next person touching it needs.

---

## `:regex()` at `root_major` — BUILT 2026-08-27

From the "grammar / argument-type gaps" bucket-list entry: `root_major`
only accepted `STAR`/`IDENTIFIER` -- no way to select among distinct
named-files/named-paths groups/named-results groups by pattern, even
though `creating references v3.txt` (lines 79-80) said it should exist.
Motivating case (David): a crowded namespace -- "acme_orders"/
"acme_invoices"/"acme_shipping" alongside another partner's
"abba_invoices" -- is more manageable when a reference can target
"/abba_.*/" vs "/acme_.*/" directly, instead of enumerating every exact
name. Design settled 2026-08-27 before building (function-only, no bare
`/pattern/` form; symmetric across all three datatypes; composes with
`'*'` traversal as a pre-filter, not a new mode) -- see that design
discussion, kept in full in the git history of this same entry's earlier
bucket-list form. Depended on `@variable` working as a function's own
direct argument (`:regex(@aregex)`), built the same day (see the entry
below).

**Built:**

- **Grammar**: `root_major: STAR | IDENTIFIER | function`
  (`reference_grammar_3.py`) -- deliberately permissive (any function,
  not a `:regex()`-specific production), mirroring how the grammar
  stays generic everywhere else and leaves "which function names are
  actually legal here" to a semantic check. Confirmed no LALR conflict
  (the grammar's own design note already required this) -- COLON
  (function) vs IDENTIFIER vs STAR are lexically distinguishable with
  zero lookahead. The transformer needed no changes at all: `root_major`
  was already a pure passthrough (`def root_major(self, value): return
  value`), so a `FunctionCall3` child (already built bottom-up by the
  existing `function` rule) just flows through unchanged.
- **`Reference3.check_valid()`** now also calls `.check_valid()` on
  `root_major` when it is a `FunctionCall3` (mirroring the same call
  already made for `name_one`/`name_three`'s own functions) -- recurses
  into a nested `InterpolatedString3`, same structural check every other
  function gets.
- **`RegexSelector3`** (new, `functions/selectors/regex_3.py`) --
  `NAME = "regex"`, `ROLE = CONTEXT_SETTER` (mirrors `Having3` exactly:
  narrows the candidate NAME set without resolving to exactly one
  entity), `DATATYPES`/`POSITIONS` cover all three datatypes at a new
  `Reference3.ROOT_MAJOR` position constant (added alongside
  `NAME_ONE`/`NAME_TWO`/`NAME_THREE`, purely for documentation/future
  type-ahead purposes -- nothing calls `_check_position()` with it, same
  as every other bare/structurally-recognized function in this
  codebase). `ARG_TYPES = (str, Regex3)` -- unlike `Name3` (where a
  plain `str` means "exact literal match", a different thing from its
  `Regex3` case), `:regex()`'s whole point is pattern matching, so a
  plain `str` arg here IS the pattern, treated identically to a
  `Regex3`'s own `.pattern` -- this is also what makes `:regex(@aregex)`
  actually usable, since a caller registering a variable via
  `set_variable()` most naturally hands over a plain Python string, not
  a v3-internal `Regex3` instance. `check_valid()` eagerly
  `re.compile()`s the pattern regardless of which arg form was used
  (mirrors `Name3`'s own eager regex-syntax check) -- fail at build
  time, not later, deep inside name matching.
- **Each finder's `query()`** gained a new `isinstance(root_major,
  FunctionCall3)` branch (checked after the existing `Star3` branch,
  before the literal-root path) -- semantically rejects any function
  other than `:regex()` (`":{name}() is not a legal root_major function
  -- only :regex() is supported"`), then `self._build(root_major)`
  (resolving `@variable` for free, via the central-eager-resolution
  mechanism built earlier the same day) and dispatches to
  `_query_star_traversal(reference, name_filter=built.pattern)` --
  structurally identical to the `Star3` case, just pre-filtered.
- **`_query_star_traversal()` in all three finders** gained an optional
  `name_filter: str | None = None` parameter, `None` meaning "every
  name," the ordinary `'*'` case, completely unchanged. Each finder
  threads it through differently, matching its own existing
  architecture rather than forcing one shape onto all three:
  - **RESULTS**: `_discover_run_homes()` already had ONE shared funnel
    point for every one of `_query_star_traversal()`'s 6 internal call
    sites -- widened its own signature to accept `name_filter` directly
    (`re.search()`'d against each entry's own group name), single-point
    change.
  - **FILES**/**CSVPATHS**: no equivalent shared funnel existed (5 and 2
    raw `named_file_names`/`named_paths_names` enumeration sites,
    respectively) -- added a new shared `ReferenceFinder3._matching_
    names(names, name_filter)` helper (filters a name list by
    `re.search()`, or returns it unchanged when `name_filter` is `None`)
    and swapped each raw enumeration site to call it.
- **`ReferenceFinder3._is_traversal_root(root_major)`** (new, shared) --
  true for `Star3` OR a `:regex()` `FunctionCall3`, as opposed to a
  literal single-entity `IDENTIFIER`. Used by
  `CsvpathsReferenceFinder3._group_manifest_entry()` (widened from an
  `isinstance(root_major, Star3)` check) to decide "could this matched
  uuid have come from any of several groups, search all of them" --
  needed for field-accessor/`:manifest()` content resolution on a
  `:regex()`-matched result to work at all. Confirmed by tracing
  (not assumed) that this is the ONLY place across all three finders'
  `_extract_data()` methods that actually needed widening -- every other
  `isinstance(root_major, Star3)` check found (FILES/RESULTS' own Rule
  1a/1b global-arrivals/archive-ledger disambiguation, both
  `Star3`-only) is specifically about a global-ledger shortcut
  `:regex()` never reaches (it has no equivalent global-ledger special
  case of its own, unlike `'*'`) and already falls through correctly to
  the ordinary per-entity handling beneath it when the check does not
  match -- confirmed by reading what each one falls through to, not by
  guessing. FILES has no `_group_manifest_entry()`-equivalent helper at
  all (its own star traversal already unconditionally rejects
  `:manifest()`/field-accessor combined with traversal outside the
  `:home()`/`:definition()` exemptions built earlier the same day), so
  needed no widening there either.

Tests: widened `test_references_3_grammar.py` (positive cases for
`:regex()` across all three datatypes including `@variable`, a negative
case confirming a bare `/pattern/` still is NOT legal directly at
`root_major`); widened `test_reference_3.py`'s `TestReference3` (a
function-valued `root_major` passes `check_valid()`, and recursion into
its own nested `InterpolatedString3` is proven); new
`test_regex_selector_3.py` (metadata, both arg forms, eager invalid-
pattern rejection); new `TestRegexRootMajor` end-to-end classes in all
three finders' own test files (crowded-namespace filtering, exclusion,
empty-match, wrong-function rejection, `@variable` form) plus a new
regex-specific case in CSVPATHS' existing `TestGroupManifestEntry` and
an end-to-end content-resolution test proving the whole chain composes.
Full local-backend suite green (3108/3108, run twice); pre-existing
SFTP/S3 env-dependent failures unrelated to this change.

## `@variable` as some other function's own direct argument — BUILT 2026-08-27

From the "grammar / argument-type gaps" bucket-list entry: `@variable`
registration and `{...}` interpolation evaluation were built 2026-08-26,
but a *bare* `@variable` used directly as some OTHER function's own
argument (e.g. `:having(@id)`, the motivating case for a future
`:regex(@aregex)`) was not -- no registered function's `ARG_TYPES`
included `Variable3`, and even if one had, nothing resolved a bare
`Variable3` to its real value (only `Variable3` *parts* nested inside an
`InterpolatedString3` were resolved). Surfaced while scoping the
`:regex()` root_major design (see that bucket-list entry) -- David:
"many functions need to support variable arguments... what does making
variables complete entail?"

**Two decisions settled first, before building (David, 2026-08-27):**
- Reference-level `@variable`s (this simple, explicit `set_variable()`/
  `set_variables()` dict registration) must NEVER be tied to a live
  running CsvPath instance's own runtime variables -- even in the
  uncertain future case of v3 references being used as productions
  within csvpath statements, only copy-by-value between the two, never
  a shared pointer. Already true in the code (`ReferenceFinder3.__init__`'s
  own comment); now also an explicit design constraint for any future
  work in this area, not just an implementation detail.
- Central, eager resolution (resolve every function's own arg once,
  right after it is built, before any finder logic touches `.arg`) over
  resolving lazily at each of the many places a finder reads some
  function's `.arg` -- "certainly for now, at least."

**Built:**

- **`ReferenceRuntimeException3`** (new, `reference_exceptions_3.py`) --
  a subclass of `ReferenceException3` (not a sibling, so every existing
  broad `except`/`pytest.raises(ReferenceException3)` keeps working
  unchanged), for problems only detectable at resolve time, not by
  `check_valid()`'s parse-time structural check. Mirrors the matching
  language's own static-vs-runtime split (`csvpath/matching/functions/
  args.py`: `Args.validate()` raises `ChildrenException` for a syntax
  problem, `Args.matches()` raises `MatchException` for a data problem
  found while matching) -- David: "we just use a different exception
  that indicates a 'runtime' error, as opposed to a static analysis
  error." Deliberately does NOT bring over that split's other half, the
  `error_manager`/`do_i_raise()` collect-vs-raise machinery -- references
  v3 has never had that, every `ReferenceException3` (this one included)
  always raises immediately. Two raise sites: an `@variable` used but
  never registered (`_resolve_value()`, both the bare-argument and the
  interpolation-part case -- the interpolation case's own existing raise
  was reclassified from the plain `ReferenceException3` it used before
  this, for the same reason), and a registered variable that resolved to
  a value of the wrong type for its argument slot (`_resolve_arg()`).
- **`Function3.check_valid()`** widened -- any function with a non-empty
  `ARG_TYPES` now also accepts a bare `Variable3`, unconditionally (not
  gated on `str` being in `ARG_TYPES`, unlike the existing
  `InterpolatedString3` widening right above it in the same method --
  reused that widening's *shape*, not its condition, since a variable's
  resolved value could be any type, not just string-shaped). A function
  declaring no argument at all (`ARG_TYPES = ()`) still rejects a
  `Variable3` too, same as any other arg. Purely structural, same as
  every other `check_valid()` check -- it cannot and does not check
  whether the eventual resolved value will actually satisfy `ARG_TYPES`.
- **`Function3.arg`** gained a setter -- overwritten exactly once, by the
  new central-resolution step below, replacing a `Variable3`/
  `InterpolatedString3` arg with its real resolved value in place.
- **`ReferenceFinder3._resolve_value()`** gained a new top-level branch
  for a bare `Variable3` (as opposed to one nested inside an
  `InterpolatedString3`'s own `.parts`, already handled) -- returns the
  RAW registered value, NOT stringified, unlike the interpolation-part
  case (which always assembles one final string) -- `:regex(@aregex)`
  needs `@aregex` to stay a real `Regex3`, not become `"/pattern/"` as
  text.
- **`ReferenceFinder3._build()`/`_build_chain()`** (new) -- wrap
  `ReferenceFunctionFactory.build()`/`build_chain()`, then resolve the
  built function's own arg in place via a new `_resolve_arg()` helper.
  Recurses into a nested function's own arg too (e.g.
  `:errors(:idchain(@pattern))` -- `ReferenceFunctionFactory.build()`
  already compiles the inner `:idchain()` into a real `Function3`
  before the outer `:errors()` is constructed, so `_resolve_arg()`
  follows the same nesting to reach it). `_resolve_arg()` is where the
  DEFERRED type check finally happens -- once the real resolved value is
  known, checked against `ARG_TYPES`, raising `ReferenceRuntimeException3`
  (not a plain `ReferenceException3`) on a mismatch, since the reference
  itself was perfectly well-formed; only the variable's own runtime
  value did not satisfy it.
- **All 14 existing call sites** across `reference_finder_3.py` and the
  three concrete finders that used to call `ReferenceFunctionFactory.
  build()`/`build_chain()` directly now call `self._build()`/
  `self._build_chain()` instead -- a mechanical swap, verified to be
  behavior-neutral for every existing (non-variable) reference by the
  full suite staying green throughout. Three methods that used to be
  `@staticmethod`s (`ResultsReferenceFinder3._pointer_from_calls()`,
  `_range_calls_from_calls()`, `_name_three_selector()`) became instance
  methods, since `self._build_chain()` needs a finder's own registered
  variables -- every existing call site already used `self.`, so this
  was safe. `ReferenceFinder3._compile_path_pattern()`'s own `:name(...)`
  handling, the ORIGINAL sole consumer of `_resolve_value()`, was
  simplified to drop its now-redundant manual `_resolve_value(built.arg)`
  call -- `self._build()` already resolves it.

**Deliberately NOT built, on request:** wiring reference-level variables
into a live, running CsvPath instance's own runtime variable store
(`variables`/`csvpath`/`headers`/`metadata`, the current v2 runtime-
reference concepts) -- explicitly ruled out as a goal here, and separate
from and much bigger than this work regardless (overlaps the standing
"v3 is not wired into production" item below). This work is scoped
entirely to the simple, explicit `set_variable()`/`set_variables()` dict
model that already existed.

**Not built either, still on the bucket list:** `:regex()` itself (the
root_major function this whole scoping exercise was originally
motivated by) -- this work unblocks `:regex(@aregex)` specifically, it
does not build `:regex()`.

Tests: widened `test_function_3.py` (Variable3 accepted for str-typed
AND int-typed `ARG_TYPES`, still rejected for no-arg functions, new
`arg` setter coverage); new `test_reference_exceptions_3.py`
(`ReferenceRuntimeException3` subclass relationship); widened
`TestResolveValue` and new `TestBuildAndResolveArg` in
`test_reference_finder_3.py` (bare-variable resolution, unregistered
raise, `_build()`/`_build_chain()` resolving in place, wrong-resolved-
type raise, nested-function-arg resolution); new end-to-end test in
`test_results_reference_finder_3.py` (`$acme.results.customers/
2025:last():having(@id)` against a real fixture, same result as the
literal-string version). Full local-backend suite green (3074/3074, run
twice); pre-existing SFTP/S3 env-dependent failures unrelated to this
change.

## A literal prefix before `:flatten()` for FILES — BUILT 2026-08-27

From the FILES `'*'`-traversal bucket-list section: `:flatten()` was
only recognized as name_one's own FIRST segment (`_is_flatten_prefixed_
reference`, built 2026-08-12 -- any depth, THEN a fixed literal/`:name(...)`
SUFFIX anchor) or as the whole of name_one (bare, any depth, no anchor
at all). A THIRD shape -- a literal/`'*'`/`:name(...)` PREFIX, THEN
`:flatten()`, THEN an OPTIONAL suffix (e.g.
`"2025/:flatten()/:name('orders.csv')"` -- "any `orders.csv` below
2025, at any depth in between") -- was explicitly deferred 2026-08-12,
David wanting it eventually but not urgently. Fell through cleanly to
`_compile_path_pattern`'s own "not a legal path segment" rejection
before this, never matching silently wrong.

**Built, purely additive as originally scoped -- does not touch the
bare or `:flatten()`-first shapes:**

- **`_is_prefixed_flatten_reference(name_one)`** (`files_reference_
  finder_3.py`) -- true when exactly one bare `:flatten()` call appears
  in `name_one.path`, NOT at index 0 (that is the existing
  `_is_flatten_prefixed_reference`'s own shape, checked first via the
  `elif` chain, so it always wins when `:flatten()` genuinely is
  first). A second `:flatten()` anywhere is not this shape either --
  falls through to the ordinary path with no special handling, which
  raises its own clear error for the extra one (no established meaning
  for two "any depth" markers in one pattern, not attempted).
- **`_matches_prefix_then_suffix(entry, home, prefix_pattern,
  suffix_pattern)`** (new static method, mirrors the existing
  `_matches_suffix`'s own shape) -- requires the file_home's relative
  segments to START WITH `prefix_pattern`, and (only if
  `suffix_pattern` is non-empty) END WITH `suffix_pattern`, with any
  number of segments (including zero) in between. An empty
  `suffix_pattern` falls out for free as "prefix, then any depth, no
  further constraint" -- e.g. `"2025/:flatten()"` alone -- the same
  "empty pattern is legal" convention `_candidates_for_name(name, [])`
  already uses elsewhere in this file, not a special case needing its
  own guard.
- **`_candidates_for_name_by_prefix_and_suffix`** -- thin wrapper
  fetching the named-file's manifest and filtering by the matcher
  above, mirroring `_candidates_for_name_by_suffix`'s own shape.

Scoped to the literal-root `query()` case only, matching the concrete
worked example exactly (`$anchor.files...`, not `$*.files...`) -- `'*'`
traversal support for this same shape was not part of this ask and was
not attempted.

Tests: new `TestPrefixedFlatten` class (`test_files_reference_finder_3.py`)
with a dedicated `PREFIXED_FLATTEN_MANIFEST` fixture proving: zero-gap
and nonzero-gap matches both count, wrong prefix excludes, wrong suffix
excludes, no-prefix-at-all excludes, `:last()`/`:first()` pick by array
order same as every other FILES pointer, a missing suffix means
"prefix then any depth," and an argument to `:flatten()` still raises.
The old stale test asserting this always raised (`test_a_literal_
prefix_before_flatten_is_not_yet_supported`, present in BOTH
`test_files_reference_finder_3.py` and, found only by running the wider
suite, a second copy in `test_normative_examples_files.py`) was updated
in both places to assert the new, real behavior rather than deleted --
confirms the same worked example is covered from the normative-examples
angle too. Full local-backend suite green (3059/3059, run twice);
pre-existing SFTP/S3 env-dependent failures unrelated to this change.

## `:having()` widened to RESULTS — BUILT 2026-08-27

From the "'*' traversal — RESULTS/CSVPATHS remaining gap" bucket-list
entry: `:having("identity")` existed for CSVPATHS only (filters a named-
paths group's own version manifest to versions whose
`named_paths_identities` contains the given identity, before any
pointer reduces). RESULTS had no equivalent.

**Clarified with David, 2026-08-27, before building** (a live-tested
finding first suggested this might be redundant with existing
capability -- worth recording since it changed the design): a literal
identity in `name_three` combined with `'*'` traversal (e.g.
`$*.results.:flatten().orders`) ALREADY does "every run's own `orders`
instance, or nothing where absent" -- confirmed live, `_results_for_run()`'s
`_find_by_identity()` lookup already returns `[]` (not an error) for a
non-matching run. That is `references_v3_expressions.md`'s own "just
give me the instances" framing for `:having()` on RESULTS, and it was
already reachable.

The REAL, previously-missing capability is different: `:having()` riding
in `name_one` (the same *slot* CSVPATHS' own `:having()` occupies, e.g.
`$acme.results.customers/2025:last():having("header_checks")`) as a
`CONTEXT_SETTER` that filters the CANDIDATE RUN POOL down to runs
containing a matching instance, BEFORE a pointer (`:last()` etc.)
reduces that pool -- returns the matching RUN itself, not the instance.
This is genuinely new: nothing in `results_reference_finder_3.py`
recognized `:having()` at all before this build (confirmed via grep).
`references_v3_expressions.md`'s own Q&A only worked out the
INTERSECT-with-CSVPATHS shape ("give me the runs") and the "just the
instances" shape (already redundant, per above) -- the run-*filtering*
shape built here is a third, equally real case neither of those two
examples covered explicitly.

**Built, mirroring CSVPATHS' own `_resolve_versions()`/`_query_star_traversal()`
precedent as closely as the two datatypes' different candidate shapes
allow:**

- **`Having3`** (`having_3.py`) widened -- `DATATYPES`/`POSITIONS` now
  include `RESULTS: (NAME_ONE,)` alongside the existing CSVPATHS entry.
  Same class, not a duplicate -- the underlying idea ("filter this
  candidate pool by whether it contains a given identity") is identical,
  just applied to a different candidate shape (run pool vs. group-
  version manifest).
- **Literal-root `query()`** (`results_reference_finder_3.py`) -- filters
  `candidates` (a list of run_home strings) right after they are sorted,
  before `:from()`/`:to()` range narrowing, using the new
  `_list_instance_identities(rh)` check (a real filesystem listing --
  RESULTS has no manifest-array field to read the way CSVPATHS'
  `named_paths_identities` provides, each run's own instance
  subdirectories ARE the identity list). `group_key_for` (`:all()`/
  `:groups()` partitioning) needed no separate trim -- its own consumer
  only ever looks up keys for `rh in candidates`, so stale entries for
  filtered-out runs are simply never read.
- **`'*'` traversal** -- `_star_run_selector_chain()` recognizes and
  exempts `having_call` from the "unsupported function" rejection
  (same treatment `all_call`/`flatten_call`/`manifest_call`/`home_call`/
  `field_call` already get), and now returns it as a fourth tuple
  element, threaded through all four of `_query_star_traversal()`'s own
  candidate-gathering branches (bare, `:flatten()`-prefixed,
  `:all()`-prefixed, plain literal/`'*'` path) into the two shared-tail
  methods, `_star_pool_and_reduce()`/`_star_group_and_reduce()`, which
  each apply the same `_list_instance_identities()` filter centrally
  (once, not duplicated across the four branches) before their own
  pointer/partition reduction. `_star_group_and_reduce()`'s own
  no-pointer delegation to `_star_pool_and_reduce()` passes no
  `having_call` (already filtered by that point) to avoid double-
  filtering.

Tests: widened `test_having_3.py`'s metadata assertions; new
`TestHavingFiltersRunsByInstanceIdentity` (literal-root, using the
existing `acme_archive` fixture's real identity split) and
`TestStarTraversalHaving` (pool mode via bare pointer/`:flatten()`,
grouped mode via `:all()`) in `test_results_reference_finder_3.py`.
Full local-backend suite green (3055/3055, run twice); pre-existing
SFTP/S3 env-dependent failures unrelated to this change.

## Results Run Manifest `named_paths_fingerprint` field — BUILT 2026-08-27 (closes issue #262)

Surfaced by David, 2026-08-26, while correcting the UNION `KIND`
taxonomy (see this file's own "UNION compatibility revised again... to
compare by conceptual `KIND`" entry below): the Results Run Manifest
(table 5) records `named_file_fingerprint` (which named-file content
drove the run) but had no equivalent field for which named-paths group
*content* drove the run — only `named_paths_uuid` (the group version's
registration identity, not its content). David's own words: "it's not,
but should be." This is what lets a run be compared, by
`:fingerprint()`/`KIND == "fingerprint"`, against the named-paths group
whose *content* (not registration event) produced it -- catching the
case where the same `group.csvpaths` text was loaded under two
different names (different uuids, identical fingerprint). Also filed
as GitHub issue #262.

**Built, mirroring `named_file_fingerprint`'s own shape exactly (same
manifest, same UNION `KIND`, same field-accessor pattern) end to end:**

- **`PathsManager.get_fingerprint_for_name(name)`** (`paths_manager.py`)
  -- new method, deliberately copy-shaped after the existing
  `get_named_paths_uuid(name)` right above it (same `None`/`"#"`-
  fragment/`"$"`-reference handling, same manifest-read-and-raise-if-
  missing shape), just returning the last manifest entry's own
  `"fingerprint"` key instead of `"uuid"`. Not factored into a shared
  helper with `get_named_paths_uuid` -- the two methods are already
  small and independently readable; extracting a helper for two
  one-line-different call sites would be the premature-abstraction
  CLAUDE.md style guidance warns against, not a real simplification.
- **`ResultsMetadata.named_paths_fingerprint`** (`results_metadata.py`)
  -- new attribute (plain `str`, unlike `named_paths_uuid`'s `UUID`
  typing/property pair -- a fingerprint is just an opaque hash string,
  same as `named_file_fingerprint`'s own plain-`str` treatment), wired
  into `from_manifest()` alongside `named_paths_uuid_string`.
- **`ResultsRegistrar.register_start()`/`metadata_update()`**
  (`results_registrar.py`) -- populates
  `mdata.named_paths_fingerprint` via
  `self.csvpaths.paths_manager.get_fingerprint_for_name(self.pathsname)`,
  right alongside the existing named-file fingerprint fetch (same
  method, same registrar, same call shape); writes it into the run
  manifest dict as `"named_paths_fingerprint"`, right alongside
  `"named_paths_uuid"`.
- **`NamedPathsFingerprint3`** (new `Function3` subclass,
  `named_paths_fingerprint_3.py`) -- `RESULTS`-only field accessor,
  `SOURCE = "manifest"`, `KIND = "fingerprint"` (the same `KIND` as
  `Fingerprint3`/`NamedFileFingerprint3` -- byte-identity is meaningful
  across different entities, per `Fingerprint3`'s own already-settled
  2026-08-26 KIND-taxonomy note), `KEY = {RESULTS: "named_paths_fingerprint"}`.
  Registered in `reference_function_factory_3.py`; `"named_paths_fingerprint"`
  added to `reference_3.py`'s `_METADATA_FIELD_FUNCTIONS` tuple. No
  finder-specific code needed anywhere -- field accessors resolve
  generically off `SOURCE`/`KEY`, and UNION `KIND` comparison
  (`reference_expression_3.py`) reads `Function3.KIND` declaratively
  off the registered class, so declaring `KIND = "fingerprint"` was
  the only wiring `ReferenceExpression3` needed.

**Deliberately scoped out, on request (David, 2026-08-27, asked
directly rather than assumed):** the SQLite (`sqlite_results_listener.py`)
and SQL (`sql_results_listener.py`/`tables.py`) integrations already
mirror `named_file_fingerprint` into their own DB schemas, but wiring
`named_paths_fingerprint` into those too would need real schema/DDL
changes (`Sqliter`'s schema.sql, a new SQLAlchemy `Column`) -- beyond
what the original bucket-list ask actually specified (function +
manifest field + registrar change, not the downstream DB integrations).
Left untouched; the field is still fully usable via
`:named_paths_fingerprint()` and directly in `manifest.json`. The OTLP
integration (`otlp_results_listener.py`) WAS wired in -- a single
additive dict key in an existing `core_meta()` override, no schema
involved, so no scope-expansion risk.

Tests: new `test_named_paths_fingerprint_3.py` (Function3 metadata/
arg-validation, mirrors `test_named_file_fingerprint_3.py`); new
`PathsManager.get_fingerprint_for_name` coverage in
`test_csvpaths_managers_paths_manager.py` (happy path against a real
`add_named_paths`-registered group, `None`-name raise, no-manifest
raise); new `ResultsMetadata` coverage in
`test_csvpaths_managers_results_metadata.py` (`from_manifest` reads
the field, defaults to `None`); extended
`test_results_reference_finder_3.py`'s existing
`test_run_scope_fields_added_2026_08_25` with the new field; extended
`test_reference_expression_3.py`'s `orders_archive` fixture with a
`named_paths_fingerprint` value and added
`test_union_of_fingerprint_and_named_paths_fingerprint_succeeds` --
the actual originally-motivating end-to-end case (`$groupa.csvpaths.
:fingerprint()` UNION `$groupa.results.:flatten():named_paths_fingerprint()`).
Full local-backend suite green (3045/3045, run twice); pre-existing
SFTP/S3 env-dependent failures unrelated to this change.

## `:home()`/`:definition()` during `'*'` traversal for FILES — three of four gaps BUILT 2026-08-27

From the "FILES '*' traversal — essentially untouched by the recent
RESULTS/CSVPATHS work" bucket-list entry, driven by David's concrete
worked example (2026-08-21): "which named-files have `on_arrival` set"
needs `$*.files.:home():definition(:on_arrival(:not_none()))`. Live
testing had identified **four independent fixes** needed, not one; this
pass builds the first three (the traversal/chaining machinery), leaving
the fourth (a predicate argument, `:on_arrival(:not_none())`) to the
separately-tracked predicate-argument entry — nothing about this build
depends on that piece, and nothing here builds toward it either, they are
genuinely independent.

**Built, in `files_reference_finder_3.py`'s `_query_star_traversal()`:**

1. **Bare `:home()` + `'*'` traversal.** `$*.files.:home()` used to raise
   `"Does not yet support :home() as a name_one path segment"` (from
   `_compile_path_pattern()`, which only recognizes `:name(...)`/clock
   functions as legal path segments — `:home()`'s zero-level-selector
   behavior was only ever wired for a literal root_major via
   `_is_bare_home_reference`, never routed through `_query_star_traversal`
   at all). Fixed by adding an `is_home` branch (new
   `_is_home_prefixed_reference()` check) that gathers `_candidates_for_
   name(name, [])` — the empty-pattern, zero-level match — across every
   named-file, same as the existing is_grouped/is_flattened/is_deep_grouped
   branches immediately above it in the same method. Deliberately NOT
   partitioned by named-file (unlike `:all()`/`:groups()`): an empty
   pattern is still a POOL-mode narrowing (one level, zero segments), the
   same peer relationship a literal/`'*'` pattern already has to plain
   `'*'` traversal's own bare-path POOL branch — a terminal pointer picks
   ONE overall winner by time across every named-file's own zero-level
   version, not one winner per named-file.

2. **Bare `:definition()` + `'*'` traversal.** `$*.files.:definition()`
   raised the identical "not a legal name_one path segment" error --
   `:definition()` was only wired for the literal-root bare case
   (`_is_bare_pointer_reference`), nothing routed it through
   `_query_star_traversal`. Unlike `:manifest()` (which has Rule 1a's real
   global ledger to fall back to at `"*"` root_major), `:definition()` has
   no equivalent global resource -- so the traversal meaning built here is
   "every named-file's own definition.json, one result per name," not a
   single shared resource. New `_is_bare_definition_reference()` check,
   early-returning (before the is_grouped/is_home/etc. dispatch) a
   `ReferenceResult3` per `named_file_names` entry, path =
   `named_file_home(name)/definition.json`, `uuid=None` (matches
   `_query_well_known_file()`'s own convention for a non-versioned
   resource). `ambiguous_content_read=True` whenever more than one result
   comes back -- Rule 1 (`manifest_field_functions_proposal.md`) still
   makes resolving full METADATA_FILE content for more than one entity at
   once illegal; `query()` itself returns every match regardless (moved
   2026-08-26, the `:path()`/Rule-1 relocation), only `resolve()`/
   `resolve_from()` raises if a caller actually tries to read more than
   one at once.

3. **Chaining `:home():definition()` together.** Even with #1/#2 built
   independently, `$*.files.:home():definition()` hit a *third*, separate
   rejection: `"does not yet support functions attached directly to
   name_one for '*' traversal"` -- a dedicated guard unconditionally
   rejects any function chained onto name_one during `'*'` traversal, so
   fixing `:home()`/`:definition()` individually did not make the
   combination work. New `_chained_definition_call()` check (only
   recognizes exactly one, argument-less `:definition()` chained onto a
   bare `:home()` -- `_is_home_prefixed_reference()`, unlike
   `_is_bare_home_reference()`, deliberately does NOT require
   `name_one.functions` to be empty, so it matches both the bare and the
   chained shape) folded into the same early-return branch as #2, but
   FILTERED to only named-files with at least one zero-level candidate
   (`_candidates_for_name(name, [])` non-empty) -- `:home()` here is a
   FILTER ("only named-files with a plain, non-templated registration"),
   not the placeholder-value role it plays bare; it has nothing to be a
   placeholder FOR, since `:definition()` doesn't vary by
   version/path the way a pointer's target would. Chaining anything OTHER
   than `:definition()` onto `:home()` during `'*'` traversal still
   raises, same as before.

**`_extract_data()` changes:** bare `:definition()` during `'*'`
traversal needed no new code at all -- `_is_bare_pointer_reference()`
never checked `root_major`, so the existing literal-root branch
(`return self._read_well_known_file(result.path)`) already fires
correctly once `query()` sets `result.path` to the right definition.json.
The chained `:home():definition()` shape needed one new branch (checks
`_chained_definition_call()` directly) since `_is_bare_pointer_reference()`
requires `name_one.functions` to be empty, which the chained shape never
satisfies.

**Deliberately scoped out of this pass, staying on the bucket list:**
FILES' `:all()`/`:groups()` GROUP modes combined with `:manifest()`/a
field-accessor (the same single-entity-vs-grouping restriction RESULTS'
`name_three` content accessor already has); a literal prefix before
`:flatten()`; `:from()`/`:to()` combined with `:all()`/`:groups()`
grouping; a literal name_three body. None of these were touched or made
easier/harder by this pass -- see the bucket list's own updated entry.

Tests: new `TestStarTraversalHome`/`TestStarTraversalDefinition` classes
in `tests/references/test_files_reference_finder_3.py` (query shape,
zero-level filtering, `ambiguous_content_read`, name_three rejection,
resolve-reads-real-bytes-per-named-file); the stale
`test_star_with_definition_is_still_not_supported` (which asserted the
OLD, now-wrong "always raises" behavior) was replaced with a comment
pointing at the new coverage. Full local-backend suite green (3036/3036,
run twice) plus the 11 known SFTP/S3 env-dependent failures (issue #216
et al., unrelated to this change).

## `:name(/regex/)` — a name_one path segment can now be a regex — BUILT 2026-08-27

From the "grammar / argument-type gaps" bucket-list entry: `Name3.
ARG_TYPES = (str,)` had no `Regex3` support, even though `Name3`'s own
docstring already flagged this as deliberately deferred ("the grammar
also allows... a regex here, but those need machinery... this first
pass does not need yet") and the grammar itself already allows a REGEX
token everywhere a STRING is allowed. Built autonomously overnight
while David was asleep, on his own instruction to pick something that
did not need him -- chosen specifically because `:idchain()` had
already settled every real design question a second `Regex3` consumer
would otherwise need decided (search(), not anchored; `re.compile` at
build time, not deferred) -- confirmed by reading `idchain_3.py`'s own
docstring before starting, not assumed, so this was applying an
already-decided design to a second consumer, not inventing one.

**Built**: `Name3.ARG_TYPES` widened to `(str, Regex3)`; `Name3.
check_valid()` (new override, calling `super().check_valid()` first)
eagerly compiles a `Regex3` arg's pattern and raises
`ReferenceException3` on a bad one, same fail-fast timing `:idchain()`
gets via its own `__init__` (`ReferenceFunctionFactory.build()` already
calls `check_valid()` right after constructing, so this fires at parse
time, not deep inside matching). A new shared helper,
`ReferenceFinder3._segment_matches(expected, actual)` (`reference_
finder_3.py`), replaces the identical `if isinstance(expected, Star3):
continue; if actual != expected: return False` block that used to be
hand-duplicated in FOUR places (`FilesReferenceFinder3._matches`/
`_matches_suffix`, `ResultsReferenceFinder3._matches_prefix`/
`_matches_prefix_at_least`) -- one shared comparison rule (`Star3` ->
always matches, `Regex3` -> `re.search()`, anything else -> `==`)
instead of four copies that would each need the same `Regex3` case
added separately. `_compile_path_pattern()` itself needed NO change --
`_resolve_value()` already passes a non-`InterpolatedString3` value
(a `Regex3` included) through unchanged, so the parsed regex lands in
the pattern list as-is, ready for `_segment_matches()`.

Tests: `test_name_3.py` (valid/invalid regex arg); new `TestSegmentMatches`
and a new `TestCompilePathPattern` case (`test_reference_finder_3.py`,
confirming a `:name(/regex/)` segment stays a `Regex3`, not unwrapped to
a string); real end-to-end FILES tests (`ALPHA_MANIFEST`'s existing
"zero.csv"/"one.csv" fixture, no new fixture needed -- `/one/` matches
only "one.csv", an invalid regex raises) and RESULTS tests (a new
two-year archive fixture, `:name(/2025/)` matches only that year's own
run). `tests/references/` now 1445 passed, up from 1433.

**`@variable` as an argument and `root_major`'s own separate `:regex()`
function gap are untouched** -- confirmed, while working on this, that
the `root_major` gap is a bigger, different question (selecting among
distinct entities, not a path segment within one already-chosen entity)
and updated the bucket list to say so explicitly, rather than leaving
it looking like a small follow-on to this fix.

---

## `ResultsReferenceFinder3._star_pool_and_reduce()`'s content-accessor guard converted — BUILT 2026-08-27

One piece of the "`'*'`-traversal content-accessor guards" bucket-list
entry, picked specifically because it was the one already marked "a
strong candidate to convert the same way" with no open caveat, unlike
its three siblings in that same entry (which either need to be decided
together with a still-untouched twin, or already proved unsafe to
convert naively once tried for the literal-root/CSVPATHS GROUP case).
Built autonomously overnight while David was asleep, on his own
instruction to pick something that did not need him.

`_star_pool_and_reduce()`'s own `if len(run_homes) > 1 and accessor is
not None: raise` (POOL mode, i.e. `pointer is None` -- every matched run
comes back unreduced) is exactly the run-level twin of the literal-root
check already converted when `:path()`/Rule 1 moved to `resolve()`:
count-based, and this specific branch has no per-partition pointer
reduction anywhere nearby to conflate with (GROUP mode is a completely
separate method, `_star_group_and_reduce`, deliberately left alone).
Converted to the same `ReferenceResults3.ambiguous_content_read`
deferred-to-`resolve()` pattern -- `query()` now always succeeds and
returns every matched run's own content-accessor results; only
`resolve()` raises if more than one run's content is actually being
read at once.

Tests: `test_no_pointer_pool_with_content_accessor_and_multiple_runs_is_rejected`
(`tests/references/test_results_reference_finder_3.py`) rewritten into
the query()-succeeds/resolve()-raises split, matching the pattern
already used for the literal-root conversions; added
`test_no_pointer_pool_with_content_accessor_and_one_run_still_works`
(new -- the positive counterpart, a single named-results group with one
run, proving a genuinely unambiguous single-run case actually resolves
real content, not just "does not raise"). `tests/references/` now 1433
passed, up from 1432.

The other three items in the parent bucket-list entry are untouched --
they either need a decision made together with a sibling, or already
proved unsafe to convert without the "was a pointer applied per
partition" reasoning the literal-root fix needed; see that entry.

---

## `#name_two` (XLSX worksheet marker) built for FILES — BUILT 2026-08-26

David, 2026-08-21: does `ReferenceResult3` need a field for which
worksheet was found? Resolved the same day: reuse `identity` (David:
"identity works quite well with worksheet (name_two)") rather than a
dedicated field. The grammar already had the slot (`name_one:
path_prefix ("#" name_two)? func_chain?`) and parsed fine, but every
finder rejected it outright the moment it was present.

**Built, `FilesReferenceFinder3` only** (CSVPATHS/RESULTS correctly keep
rejecting it as files-only, unchanged): `query()`'s old unconditional
rejection replaced with two narrower, precise ones -- `#name_two`
combined with a bare context-setter/marker function occupying name_one's
entire content (`:all()`/`:manifest()`/`:home()`/etc. -- anything other
than `:name(...)`, which is path-BUILDING, not a marker, same exemption
`_is_bare_function_only` already makes) still raises, since there is no
literal file to have a worksheet in; combined with a literal path but no
version-selecting pointer in name_three also still raises (checked at
both the no-name_three-at-all point and the has-name_three-but-no-
pointer point), since there is no single version to read a worksheet
from. Otherwise legal now -- the matched `ReferenceResult3`'s own
`identity` is populated with the worksheet name at `query()` time.

`_extract_data()`'s `FIRST_PARTY` branch reads the named worksheet by
appending `#{worksheet}` to the matched file's own path before handing
it to `DataFileReader` -- which already understood this exact
`path#sheet` convention (`file_readers.py`'s own `__new__`), no new
reading mechanism invented. Confirmed, not assumed, that the ordinary
`reader.source.read()` every other `FIRST_PARTY` read uses does NOT work
for XLSX before writing around it: `XlsxDataReader` is row-oriented
(`.next()`, a generator of `list[str]` rows via `pylightxl`), never sets
`.source` at all -- the ABC's own `.read()` docstring already flagged
this ("may not work as-is for some files, e.g. xlsx... today we only
need it for csvpaths files"). Explicitly rejects a non-XLSX path
(`XlsxReaderHelper.is_xlsx()`) rather than silently falling through to
whatever reader the stripped path happens to resolve to.

Tests use a real, already-shared XLSX fixture
(`tests/csvpaths/test_resources/Book1.xlsx`, also used by
`tests/csvpaths/test_csvpaths_xlsx.py`, with two known real worksheets,
"hello" and "world") rather than a synthetic one, for both `query()`
(`identity` populated) and `resolve()` (actual rows read, and the two
worksheets give different rows -- proves the sheet argument really
selects, not just parses). `tests/references/` now 1432 passed, up from
1426.

**Deliberately did not touch `_query_star_traversal()`'s own separate
`#worksheet` rejection** -- see the bucket list's new entry for this,
same scoping discipline as the recent `:path()`/`:home()` work.

---

## `:home()`'s field-read job split into four scope-specific functions — BUILT 2026-08-26

David, 2026-08-21, refined 2026-08-24: no manifest anywhere has a literal
`"home"` key — `Home3.KEY` read `file_home` (FILES), `named_paths_home`
(CSVPATHS), `run_home` (RESULTS run scope), `instance_home` (RESULTS
instance scope), never a bare `"home"`. `:home()` did two jobs under one
name: reading whichever of those four real keys a pointer already
selected, AND acting as the zero-level ("no template") placeholder when
used bare, alone, as `name_one`'s entire content. Only the field-read job
is retired — David, 2026-08-24, explicit: "`:home()` as the means of
accessing the 0-level template files and results has to remain... I
can't think of a better name for the function."

**Built**: four new field-accessor functions, one per real key --
`FileHome3`/`:file_home()` (FILES, `KEY = {FILES: "file_home"}`,
`POSITIONS = {FILES: (NAME_THREE,)}`), `GroupHome3`/`:group_home()`
(CSVPATHS, `KEY = {CSVPATHS: "named_paths_home"}`, `POSITIONS =
{CSVPATHS: (NAME_ONE,)}` -- CSVPATHS' entire share of the old job, since
it has no zero-level concept to leave anything behind for),
`RunHome3`/`:run_home()` (RESULTS run scope, `KEY = {RESULTS:
"run_home"}` only -- deliberately does NOT also declare a `RESULT` key
the way `:home()` used to, since it is meant to be scope-specific, not
polymorphic), `InstanceHome3`/`:instance_home()` (RESULTS instance
scope, `KEY = {RESULT: "instance_home"}` only, symmetric reasoning).
Confirmed each one's own `KEY` dict is looked up correctly before
assuming it: FILES/CSVPATHS' generic `function_cls.KEY.get(reference.
datatype)` dispatch needed nothing new (single-scope datatypes), but
RESULTS' own `_extract_data()` has two SEPARATE, hardcoded call sites
(`function_cls.KEY.get(Reference3.RESULTS)` for a name_one-riding run-
level field, `function_cls.KEY.get(Reference3.RESULT)` for a name_three-
riding instance-level one) -- each new function's single-entry `KEY`
dict lines up with exactly one of those two call sites, by construction,
not by coincidence.

`Home3` itself narrowed to the placeholder role only: `SOURCE`/`KEY`
removed entirely (nothing reads a manifest field off it anymore),
`DATATYPES` narrowed to `(FILES, RESULTS)` (CSVPATHS dropped -- no
zero-level concept), `POSITIONS` narrowed to `{FILES: (NAME_ONE,),
RESULTS: (NAME_ONE,)}` (the ordinary field-accessor positions --
`NAME_THREE` for FILES, the same `NAME_ONE` slot but riding beside a
real pointer for RESULTS -- both removed). Also removed `"home"` from
`Reference3._METADATA_FIELD_FUNCTIONS` and added the four new names --
confirmed necessary the hard way: `resolve_kind` dispatches off that
hardcoded tuple (a separate, already-flagged piece of debt, not touched
here beyond this one addition), so the new functions silently resolved
to `FIRST_PARTY`/raw-bytes reads instead of their own manifest field
until this was added, caught by the test suite (`FileNotFoundError`
trying to open a directory as a CSV file) rather than assumed correct.

**A second regression caught by the test suite, not assumed safe**:
`ResultsReferenceFinder3._star_run_selector_chain()`'s own `'*'`-
traversal validation used to exempt `:home()` from the "no unknown
non-pointer function" rejection only as a side effect of it being
recognized as a field accessor (`SOURCE is not None`) -- once `:home()`
lost `SOURCE`, that exemption silently disappeared too, breaking
`$*.results.:home()` (previously-shipped, tested behavior). Fixed by
adding an explicit, separate `:home()`-by-name exemption alongside the
existing `:all()`/`:flatten()`/`:manifest()` ones, rather than
special-casing `SOURCE` again.

**Compendium's own now-stale claim** ("`:home()` reverts to its ordinary
job of reading the field once a pointer joins the chain") still needs
fixing -- not touched here, since David is mid-edit on that file
directly; flagged to him instead of editing around him.

Tests: `test_home_3.py` rewritten for the narrowed shape (`SOURCE is
None`, `KEY == {}`, narrowed `POSITIONS`); four new unit-test files,
one per new function (`test_file_home_3.py`/`test_group_home_3.py`/
`test_run_home_3.py`/`test_instance_home_3.py`), mirroring
`test_named_file_home_3.py`'s own style. Rewrote every existing
finder-level test that exercised the old field-read job through
`:home()` itself (FILES: `test_home_in_name_three_position_is_
unaffected` -> `test_home_in_name_three_position_now_raises` (new,
proves the retirement is enforced) plus `test_file_home_in_name_three_
position_works`; two `test_home` methods -> `test_file_home`;
CSVPATHS: `test_home`/`test_home_reads_named_paths_home` ->
`test_group_home`/`test_group_home_reads_named_paths_home`; RESULTS:
`test_home_at_run_scope_reads_run_home`/`test_home_at_instance_scope_
reads_instance_home` -> `test_run_home_at_run_scope_reads_run_home`/
`test_instance_home_at_instance_scope_reads_instance_home`) --
every bare/zero-level-placeholder `:home()` test (the much larger
share) is untouched, still passing unchanged. `tests/references/` now
1426 passed, up from 1414.

---

## `:path()` retired; Rule 1 enforcement moved from `query()` to `resolve()` — BUILT 2026-08-26

David, 2026-08-22: **getting paths is not the same as accessing files.** A
field/file accessor trying to read *content* for more than one matched
entity is illegal, no argument — but a `query()` that merely points to
multiple entities is fine in principle. `:path()` existed only to route
around Rule 1's `query()`-time restriction (wrap a whole-resource content
function, return its path instead of content, since a path is cheap/
poolable); that whole function becomes redundant once the restriction
itself moves to `resolve()`. David's decision: **`query()` should always be
allowed to return multiple matches, regardless of accessor; only
`resolve()` (actually reading content) raises when asked to resolve more
than one at once.**

**Scope, decided while implementing, not just assumed**: only each finder's
own LITERAL-root `query()` method was touched — the bucket list's own
"likely a bigger simplification... re-audit case by case" caution turned
out to be well-founded once actually tried (see below); the `'*'`-traversal
guards are deliberately left exactly as they were, as a new, more specific
bucket-list entry enumerating the concrete candidates.

**Built**:
- `Path3`/`csvpath/references/functions/wrappers/` (the whole package,
  `Path3` was its only file) deleted; factory registration removed.
  `ReferenceFinder3._find_path_call`/`_resolve_path_call` (the shared
  helpers `:path()` used) removed — nothing calls them anymore.
- `ReferenceResults3` gained a new field, `ambiguous_content_read: bool =
  False` (`reference_results_3.py`), and `select()` propagates it. Set by
  a finder's own `query()` when it found more than one raw, unreduced
  candidate for a whole-resource content accessor (`:manifest()`,
  `:definition()`, `:errors()`, etc.) with no pointer to pick one — Rule 1
  still makes this illegal, but `query()` no longer raises for it.
- `ReferenceFinder3.resolve_from()` (`reference_finder_3.py`) now raises
  if `results.ambiguous_content_read and len(results) > 1`, instead of
  each finder raising inside `query()` itself. `resolve()` is unaffected
  otherwise (still `resolve_from(query())`).
- `FilesReferenceFinder3.query()`, `CsvpathsReferenceFinder3.query()`,
  `ResultsReferenceFinder3.query()` (their own literal-root branches only)
  no longer raise for "no pointer + more than one matching version/run +
  a content accessor" — each now computes the same condition it used to
  raise on and passes it as `ambiguous_content_read` on the
  `ReferenceResults3` it returns instead.

**A naive version of this broke a legitimate, already-shipped case, caught
by the existing test suite rather than assumed safe**: the first attempt
computed `ambiguous_content_read` (or, before that flag existed, a raw
`resolve_kind == METADATA_FILE and len(final_results) > 1` check) purely
from the FINAL result count, which incorrectly rejected
`$acme.csvpaths.:all():last():manifest()`-style GROUP-mode traversal
(several named-paths groups, each already reduced to its OWN one manifest
entry by the `:last()` pointer applied WITHIN each group/partition) —
legitimate and already tested, even though the final count is > 1. The
fix: the flag is computed by each finder's own `query()`, which alone
knows whether a pointer actually reduced ITS candidates — not a generic
post-hoc count check computed once, centrally, from the final list alone.
Confirmed, live, that `_resolve_versions()`/`_apply_pointer()` already
guarantee at most one candidate whenever a pointer was actually present,
for all three finders, before relying on that guarantee.

**Deliberately did NOT convert every `'*'`-traversal content-accessor
guard** — several are unconditional/syntax-based rejections ("not yet
supported," not a count-dependent Rule 1 check), and one further deferred
count-based one (`ResultsReferenceFinder3._query_star_traversal()`'s own
instance-level `match_all + accessor` check) was left as an immediate raise
deliberately, since no established case needs it to succeed even when it
happens to match exactly one instance — see the bucket list's new,
specific entry for exactly which guards remain and why each one is/isn't
an obvious candidate.

Tests: rewrote the `query()`-time-raise tests that the bucket list itself
flagged as needing rewriting, not deleting (`TestManifestCombinedWithNameThree`
in `test_files_reference_finder_3.py`, plus the CSVPATHS/RESULTS
equivalents) into `query()`-succeeds-with-`len() > 1`/`resolve()`-raises
pairs. Deleted `TestPathFunction` (four files: `test_files_reference_finder_3.py`,
`test_csvpaths_reference_finder_3.py`, `test_normative_examples_files.py`,
`test_normative_examples_csvpaths.py`) and `tests/references/functions/
wrappers/test_path_3.py` entirely — the function no longer exists. Full
`tests/references/` suite: 1413 passed (down from 1428 before this PR,
net of 15 `:path()`-specific tests removed and no tests added, since every
other rewritten test kept the same coverage under the new split).

`manifest_field_functions_proposal.md`'s own Rule 2 (design-notes file,
kept as history rather than rewritten) annotated "RETIRED 2026-08-26"
rather than deleted, matching that file's own existing convention of
inline revision notes.

---

## Fingerprint functions grouped under `KIND = "fingerprint"` — CORRECTED 2026-08-26

Fourth revision, same conversation, same day, of `UNION`'s own
compatibility rule -- corrects a call made in the entry two below this
one ("UNION compatibility revised again, to compare by conceptual
KIND"), which had deliberately left `:fingerprint()`,
`:named_file_fingerprint()`, and `:file_fingerprints()` uncategorized,
reasoning from `Fingerprint3`'s own pre-existing docstring that they
describe different entities' content and should stay separate. Flagged
that reasoning to David transparently rather than silently overriding
it either way; David pushed back directly:

> There is some truth to it, but it is not ironclad. If a named-paths
> group fingerprint were carried into a run manifest (it is not, but
> should be), we would name the run manifest field
> named_paths_fingerprint, but compare it to `:fingerprint()` on the
> named-paths group side. And that is one clearly valuable case:
> group.csvpaths files may exist under different names having been
> loaded from the same csvpaths text. We would want to be able to
> signal that and `:uuid()` will not do it. Ultimately, a fingerprint is
> a cryptographic identity of bytes... we care that two UUIDs are
> distinct in one way and two fingerprints are distinct in another way
> -- and the way that fingerprints are distinct is that bytes are
> either the same or they are not.

The distinction that actually matters: a uuid is an identity of an
*entity/event* (a registration, a run), so two different entities always
get different uuids even with byte-identical content; a fingerprint is
an identity of *content*, so it is meaningful to ask "is this the same
content" across two entirely different entities/manifests. That is
precisely why grouping the fingerprint functions together is correct
where grouping, say, `:fingerprint()` with `:uuid()` would not be.

**Built**: `KIND = "fingerprint"` added to `Fingerprint3`
(`fingerprint_3.py`), `NamedFileFingerprint3`
(`named_file_fingerprint_3.py`), and `FileFingerprints3`
(`file_fingerprints_3.py`, despite being dict-shaped -- UNION only cares
about accessor comparability, never resolved-value shape, so the
dict-vs-scalar difference does not disqualify it; `SUBTRACT`/`INTERSECT`
still separately reject a dict-valued join key via `_hashable`,
unaffected). Rewrote `Fingerprint3`'s own docstring (previously said
"deliberately not unified with... those describe the fingerprint of
other content... not of the entity itself" -- now explains the opposite
conclusion and why) and `NamedFileFingerprint3`'s docstring to match.

**Also surfaced, and added to the bucket list, a genuine gap David named
directly**: the Results Run Manifest has no `named_paths_fingerprint`
field today (only `named_paths_uuid`, an identity-of-registration-event
field, not identity-of-content) -- see the bucket list's own new entry.
Not built now; this was raised as a hypothetical motivating example, not
a request to build it in this pass.

Tests: added `test_union_of_fingerprint_and_named_file_fingerprint_succeeds`
(`tests/references/test_reference_expression_3.py`) -- `$groupa.csvpaths.
:fingerprint()` UNION `$groupa.results.:flatten():named_file_fingerprint()`,
proving the cross-entity, cross-function `KIND` match actually resolves
end to end, not just that it does not raise. Required adding a
`fingerprint` key to `GROUPA_MANIFEST` and an optional
`named_file_fingerprint` kwarg to the `_make_run()` fixture helper.
`tests/references/` now 1428 passed, up from 1427.

---

## `ReferenceExpression3` UNION compatibility rule revised to LHS-driven accessor-equality — BUILT 2026-08-26

Same day as the `paths`-vs-`values` matrix entry below, but a genuine
revision of it, not a duplicate — David reopened `UNION`'s own compatibility
check almost immediately after that build landed, via a design note about
"`UNION` of paths": bare-path `query()`-level unions (no field accessor on
either side) need to work without regard to uuid or any resolved data, and
the boundary condition ("LHS resolves to a value that does not match the
type of RHS's value -> raise") needed a real mechanism, not just prose.

Worked through in conversation, not assumed:
- First clarified whether the rule was meant to be symmetric or driven by
  one side — David: **genuinely LHS-driven**, not symmetric (confirmed
  directly, not inferred).
- Then how "does not match the type" should actually be checked -- runtime
  value-type comparison (`isinstance`/`type()` on resolved `.data`) vs.
  something declarative. David's own proposal, verbatim: *"could we not do
  it by comparing functions? a `:uuid() == :uuid()`, `:type()` may or may
  not equal `:type()`, `:type("csv") != :type("xlsx")`. So the accessor
  must equal. If it does, we then ask are the values equal?"* -- i.e.
  compare each side's own terminal `FunctionCall3` (function name +
  argument together) for structural equality, not the resolved values'
  runtime types. Confirmed `FunctionCall3.__eq__` (`reference_3.py`)
  already does exactly this comparison (`name` + `arg`), so no new
  comparison primitive was needed, only wiring it into `UNION`'s own
  check.
- This deliberately **replaces** the earlier `PRODUCES_UUID`-based "both
  sides produce a uuid" framing from the original design note, rather than
  layering a separate uuid-specific tier on top of it: `:uuid()` and
  `:run_uuid()` both produce a uuid but are not the *same* accessor, so
  under the final rule they are NOT union-compatible, even though they
  would be directly comparable under `SUBTRACT`/`INTERSECT`'s own
  uuid-valued-RHS case (a genuinely different, still-unchanged rule --
  see the matrix entry below). `:uuid() == :uuid()` and a bare `:type()`
  against another bare `:type()` are both still fine (identical accessor);
  `:type("csv")` vs. `:type("xlsx")` is not (same function, different
  argument).

**Built**: `ReferenceExpression3._terminal_value_call()` (new, returns the
side's own terminal `ROLE == VALUE` `FunctionCall3`, or `None` for a
`paths` side -- `_kind()` rewritten as a one-line consumer of it) and
`_check_union_compatible()` (new, replaces the inline symmetric check
`resolve()` used to run for `UNION` -- if LHS is `paths`, returns
immediately (RHS unions freely, by path); otherwise raises unless RHS's
own terminal `FunctionCall3` equals LHS's, via the existing `__eq__`).
`resolve()`'s `UNION` branch is now just `self._check_union_compatible();
return self._union(...)`.

**Also resolves the separate, previously-open "`ReferenceExpression3` has
no `query()`-only mode" bucket-list item** (found 2026-08-24, compendium
4.2) -- decided, in the course of this same conversation, NOT to build a
distinct `query()`-only code path. The compatibility check itself was
already purely structural (parsed accessors, never resolved data) before
this revision and stays that way; `resolve()` remains the sole public
entry point and still fully resolves both sides regardless of kind --
there was never a real cost to resolving that a `query()`-only shortcut
would have avoided, once the check moved to comparing parsed accessors
rather than resolved values.

Tests: rewrote `TestPathsVsValuesEndToEnd.test_union_of_a_paths_side_and_a_values_side_raises`
(`tests/references/test_reference_expression_3.py`) into three tests
reflecting the new asymmetric rule --
`test_union_of_a_paths_left_and_values_right_succeeds_by_path` (no longer
raises -- LHS `paths` unions freely),
`test_union_of_a_values_left_and_paths_right_raises` (new -- the reverse
order now matters), and
`test_union_of_two_values_sides_with_different_accessors_raises` (new --
`:named_paths_name()` vs. `:run_uuid()`, both `values` but not the same
accessor). Updated `references_v3_expressions.md`'s own matrix and
"Why SUBTRACT/INTERSECT's raise is asymmetric" section to describe the
new rule instead of the superseded symmetric one.

**Superseded within the hour** -- see the entry above this one
("`ReferenceExpression3` UNION compatibility revised again, to compare
by conceptual `KIND`"). David reopened this almost immediately: the
"accessor must be literally identical" rule above is exactly what makes
`:uuid()`/`:run_uuid()` incompatible, which turned out not to be what he
actually wanted once he worked through it further with a concrete
worked example. The `_terminal_value_call()`/`_kind()` machinery built
here is unchanged; only `_check_union_compatible()`'s own comparison
(and the now-generalized `Function3.KIND`, replacing `PRODUCES_UUID`)
changed again.

---

## `ReferenceExpression3` UNION compatibility revised again, to compare by conceptual `KIND` — BUILT 2026-08-26

Same conversation, same day, third and (so far) final revision of
`UNION`'s own compatibility rule. David reopened the "accessor must be
literally identical" rule (the entry directly below this one) almost as
soon as it was confirmed, pasting back his own original design note with
one new closing paragraph added:

> Note that in the 3rd example the RHS's INTERSECT is compared by
> function type and retrieved value. `:fingerprint()` retrieves a
> string. The reference would not accept a comparison of
> `:fingerprint()` to `:type()` because the function types do not serve
> the same conceptual purpose, making the values not the same,
> regardless of actual bytes value. A comparison of
> `:named_paths_name()` to `:named_results_name()` would work because
> names are conceptually the same kind of thing. This makes it important
> to know the purpose of the function in order to use it correctly for
> comparison. `:uuid()` and `:run_uuid()` are comparable.
> `:named_file_name()` and `:fingerprint()` are not.

This directly contradicts the literal-identity rule just built (which
would have rejected `:uuid()`/`:run_uuid()`) -- confirmed with David
before touching code, since the taxonomy of "which functions share a
conceptual purpose" spans dozens of field-accessor files and is a real
judgment call, not something safely inferred. Proposed a concrete
mechanism plus a first-pass taxonomy (uuid/name/fingerprint/type
groups); David: "Yes, that is perfect."

**Built**: `Function3.PRODUCES_UUID: bool` generalized into
`Function3.KIND: str | None` (`function_3.py`) -- a declarative
conceptual-family tag, not just a uuid-specific flag. Set `KIND =
"uuid"` on the same four functions that used to set `PRODUCES_UUID =
True` (`Uuid3`, `RunUuid3`, `NamedFileUuid3`, `NamedPathsUuid3`); set
`KIND = "name"` on `NamedPathsName3`, `NamedResultsName3`,
`NamedFileName3`. `ReferenceExpression3._check_union_compatible()`
rewritten: compatible if the right side's terminal accessor shares the
left's own non-`None` `KIND`, OR (regardless of `KIND`) the two
accessors are literally identical -- the second branch is what keeps a
bare `:type()` comparable to another bare `:type()` even though `:type()`
has no declared `KIND` of its own. `_produces_uuid()` (still used by
`SUBTRACT`/`INTERSECT`'s own, separate, unchanged uuid-valued-RHS case)
now checks `KIND == "uuid"` instead of the retired `PRODUCES_UUID`.

**Deliberately did NOT group the fingerprint functions**, despite an
initial proposal to do so, which David approved before this specific
tension was noticed while re-reading the code: `Fingerprint3`'s own
existing docstring already explains why it is "deliberately not unified
with... `named_file_fingerprint` or... `file_fingerprints`" -- those
describe the fingerprint of a *different* entity's content (the
named-file input a run/instance consumed), not the resolved entity's
own content. Grouping them under one `KIND` would have directly
contradicted that already-settled reasoning. Left `Fingerprint3`,
`NamedFileFingerprint3`, `FileFingerprints3`, and `Type3` all with no
declared `KIND` for now (falls back to the literal-identity rule) --
flagged to David as a discovered tension rather than silently
overridden either way; revisit if/when a real cross-entity fingerprint
comparison use case actually comes up.

**Corrected within the hour** -- see the entry above this one
("Fingerprint functions grouped under `KIND = \"fingerprint\"`"). David
pushed back on the "different entities can never share a `KIND`"
reasoning directly: a fingerprint is a cryptographic identity of BYTES,
not of an entity, so it is exactly the kind of value that should be
comparable across different entities/manifests -- unlike uuid/name.
`Type3` alone stays uncategorized -- unaffected by the correction.

Tests: renamed `test_union_of_two_values_sides_with_different_accessors_raises`
to `test_union_of_two_values_sides_with_different_kinds_raises` (still
raises -- `:named_paths_name()` is `KIND "name"`, `:run_uuid()` is `KIND
"uuid"`); added `test_union_of_two_values_sides_with_the_same_kind_succeeds`
(`:uuid()` vs. `:run_uuid()` -- the concrete case the literal-identity
rule got wrong) and `test_union_of_two_name_accessors_with_the_same_kind_succeeds`
(`:named_paths_name()` vs. `:named_results_name()`), both in
`test_reference_expression_3.py`. Widened the four uuid functions' own
`PRODUCES_UUID` assertions to `KIND == "uuid"`. `tests/references/` now
1427 passed, up from 1425.

---

## `ReferenceExpression3` `paths`-vs-`values` compatibility matrix — BUILT 2026-08-26

Settled 2026-08-23 (see `references_v3_expressions.md`'s own "`paths` vs.
`values` sides" section for the full matrix) while working through what
should happen when one side of a `UNION`/`SUBTRACT`/`INTERSECT` has no
trailing `VALUE`-role accessor (`paths` -- plain path+uuid) and the other
does (`values` -- a real scalar in `.data`). Live-traced the current code
first (`reference_expression_3.py`'s `_intersect`/`_subtract`/`_keys`) to
find the actual behavior, not just what the semantics notes claimed:
`None`-valued `.data` (what every `paths`-side item had) was silently
treated as "never matches" — `INTERSECT` with a `paths` side quietly came
back empty, `SUBTRACT` quietly came back as an unfiltered copy of the
left side, in every case, with no error. A real, currently-shipped gap,
not just an untested edge case.

**Continued straight through the bucket list, per David's own "step
through in order unless you spot a better one" instruction, then flagged
a real ordering issue**: the item ahead of this one (`ReferenceExpression3`
query()-only mode) explicitly needed a yes/no decision before any code
made sense ("worth deciding whether... actually wanted... not yet
designed"), while this one had an already-settled design and a confirmed
live bug. David: skip ahead to this one now, circle back to the decision
-needed one after.

**Built, all four pieces the bucket-list entry named**:
- **The `paths`/`values` classifier** (`ReferenceExpression3._kind()`) —
  static, from the parsed reference's own `terminal_functions` (see
  below), checking each function's own `ROLE` directly against the
  registry (`ReferenceFunctionFactory`) rather than via `Reference3.
  resolve_kind`'s hardcoded name tuples — deliberately avoiding a second
  consumer of that already-flagged debt (see the `resolve_kind` bucket-
  list entry, still open). A side is `VALUES` if its terminal chain
  includes any `ROLE == Function3.VALUE` function, `PATHS` otherwise.
- **`Reference3.terminal_functions`** (`reference_3.py`) — extracted as a
  new public property from what used to be `resolve_kind`'s own inline
  computation (pure refactor, `resolve_kind` itself unchanged/untouched
  behavior, still hardcoded-tuple-based) — needed so the classifier
  above computes the same terminal chain without duplicating the
  traversal logic.
- **`UNION` validation** — raises if the two sides' kinds differ
  ("concatenating two structurally different result shapes into one bag
  is never meaningful, regardless of order"). **Superseded later the same
  day** — see the entry above this one ("`ReferenceExpression3` UNION
  compatibility rule revised to LHS-driven accessor-equality"), which
  replaces this symmetric kind-check with David's own "compare the
  accessors, not the value types" rule. `_kind()` itself, and everything
  else in this entry (the classifier, `terminal_functions`, the
  `SUBTRACT`/`INTERSECT` rewrite, `PRODUCES_UUID`), is unaffected — only
  `UNION`'s own check changed.
- **`SUBTRACT`/`INTERSECT` rewrite** — `values`/`values` unchanged
  (compare by `.data`, the existing `_intersect`/`_subtract` methods,
  untouched); two new comparison methods for the other three matrix
  rows: `_filter_by_identity()` (`paths`/`paths`, or `values`(LHS)/
  `paths`(RHS) — compares `(path, uuid)` tuples, LHS's own `.data` if any
  survives unchanged in the output) and `_filter_by_native_uuid()`
  (`paths`(LHS)/`values`(RHS) where RHS is uuid-valued — LHS's own
  native `.uuid` compared directly against RHS's `.data`). `resolve()`
  itself now branches on `right_kind` first (covers both identity-basis
  rows in one check), then `left_kind` if right is `values` (raises, or
  falls back to native-uuid comparison, per the matrix).
- **`Function3.PRODUCES_UUID`** (new declarative class attribute,
  default `False`) — checked generically by `ReferenceExpression3`, not
  hardcoded by function name, same `POSITIONS`/`_check_position()`
  precedent already established elsewhere. Set `True` on the four
  functions that genuinely produce a uuid: `:uuid()`, `:run_uuid()`,
  `:named_file_uuid()`, `:named_paths_uuid()` — confirmed by reading each
  one's own `KEY`, not assumed from the name alone.

Tests: `TestFilterByIdentity`/`TestFilterByNativeUuid` (synthetic-
`ReferenceResults3` unit tests, mirroring the existing `TestIntersect`/
`TestSubtract` style) plus `TestPathsVsValuesEndToEnd` (5 real, end-to-
end tests through `resolve()` and the existing `orders_archive` fixture
— UNION-mismatch-raises, `paths`/`paths`, `values`(LHS)/`paths`(RHS)
keeping LHS's own `.data`, `paths`(LHS)/`values`(RHS) non-uuid-valued
raising, and the uuid-valued case actually matching) in
`test_reference_expression_3.py`; `TestTerminalFunctions` in
`test_reference_3.py`; widened `PRODUCES_UUID` assertions in all four
uuid functions' own unit tests. `tests/references/` now 1423 passed, up
from 1408.

---

## `Function3.describe()`'s markdown-rendering companion — BUILT 2026-08-26

Compendium 5.4: "Reference functions are self-documenting... must be
able to output .md in a similar way to `csvpath/cli/function_describer.py`."
`Function3.describe()` already existed but only returned a plain dict
(`name`/`summary`/`role`/`datatypes`) meant for a future type-ahead
layer, not human-readable output — the actual rendering layer 5.4
requires didn't exist.

**Built as a new, separate class** (`Function3Describer`, `csvpath/
references/function_describer_3.py`), not a reuse of the match-language
`FunctionDescriber` and not a change to `Function3.describe()` itself
(left alone — still the machine-readable half, unchanged contract).
Match-language functions have argsets/overloads/qualifiers that
references-v3 functions simply do not (at most one arg, no overloads at
all), so a from-scratch, much simpler renderer fit the actual `Function3`
model better than adapting the heavier match-side one. Two entry
points: `describe(function_cls)` (one function's own markdown block —
name, summary, role, datatypes, argument type/required-ness, `POSITIONS`
per datatype, and — for field accessors — `SOURCE`/`KEY`/`LEDGER_KEY`/
`BARE_SOURCE` when declared) and `describe_all()` (the whole registry as
one combined document: an alphabetical index linking down to each
function's own block, mirroring `FunctionDescriber.describe()`'s own
"[[Back to index]]" convention, just inverted — one document, not one
page per function).

New `ReferenceFunctionFactory.registered_names()` (`reference_function_
factory_3.py`) — `describe_all()` needed to enumerate every registered
name without reaching into the factory's own "private" `_FUNCTIONS` dict
from outside the class.

**Deliberately just a markdown-STRING producer** — writing the result to
a file, or wiring it into any interactive CLI (the way `FunctionLister`
wires the match-language version into a REPL picker), is a separate
integration question, out of scope here (v3 is not wired into
production yet, see this list's own "Bigger, standing items"). Also
deliberately side-stepped GitHub-flavored-markdown's own heading-to-
anchor slugify ambiguity (different renderers handle punctuation in
headings differently) by keeping each function's own heading a plain
`## {name}` with no backticks/colon/parens, so the index's own `#{name}`
links resolve predictably everywhere rather than replicating one
specific renderer's exact algorithm.

Tests: `tests/references/test_function_describer_3.py` — one function's
own block (name/summary/role/datatypes/argument-required-ness/source-
key/bare-source/positions, spot-checked against `Year3`/`Idchain3`/
`Template3`), plus `describe_all()` (every registered name appears in
the index exactly once, one full block per function, no duplicates).
`tests/references/` now 1408 passed, up from 1397.

---

## Predicate support functions (5.31), plus the `:idchain()` filter half of predicate-argument accessors — BUILT 2026-08-26

Found 2026-08-24 (Phase 1 compendium review). The compendium lists eight
predicate-support functions: `:true()`, `:false()`, `:none()`,
`:not_none()`, `:empty()`, `:not_empty()`, `:regex(/.../)`, `:having(...)`.
Only `:having()` existed. `:regex()` as a *function* (distinct from
`Regex3`, the `/pattern/` literal type) stays tracked separately under
the grammar/argument-type-gaps entry, not double-counted here.

**Same entanglement risk as the date/time functions (previous entries)
— the six leaf functions would be inert without a real consumer.**
Continuing straight through the bucket list in order (David's own
call — "step through the items unless you spot a better ordering"),
but the natural, already-*settled* consumer wasn't a later list item at
all — it was sitting right there in the still-open "Predicate-argument
field accessors" entry: compendium 5.36/§4.13/4.14 had already agreed
`:idchain()` should accept a predicate argument (`:errors(:idchain(
:not_none()))` — "any idchain at all", a filter), with `Idchain3.
ARG_TYPES` widening explicitly named as the one remaining, ready-to-
build piece. Wired that in the same pass, rather than leaving the six
functions with zero consumers the way a stricter "one bucket item at a
time" reading would have.

**Built**: `:true()`/`:false()`/`:none()`/`:not_none()`/`:empty()`/
`:not_empty()`, all `ROLE = VALUE`, `DATATYPES = (FILES, CSVPATHS,
RESULTS)` (datatype-agnostic, matching how they are meant to nest
inside any field accessor's argument regardless of datatype, even
though the one consumer wired up so far is RESULTS-only). New shared
base class, `PredicateFunction3` (`csvpath/references/functions/
filters/predicate_function_3.py`), each declaring `matches(value) ->
bool` — added specifically so a consumer (e.g. `Idchain3`) can declare
`ARG_TYPES` generically as `(..., PredicateFunction3)` instead of
enumerating all six concrete classes by name, matching the project's
own declarative-over-hardcoded-list preference (see the `resolve_kind`
bucket-list entry) — a future predicate function automatically works
with any existing consumer with no changes there at all.

`Idchain3.ARG_TYPES` widened to `(str, Regex3, PredicateFunction3)`;
`Idchain3.matches()` now delegates to the nested predicate's own
`matches()` when `self._arg` is one, checked before the existing str/
Regex3 branches. No special-casing needed for how a predicate function
actually gets built as `:idchain()`'s own arg — `ReferenceFunctionFactory.
build()` already recursively builds a nested `FunctionCall3` arg into a
real `Function3` instance (the same generic mechanism `:from(:index(2))`
already relies on), confirmed live before assuming it would "just work".

**Still explicitly NOT built** (separately tracked, see the bucket
list's own "Predicate-argument field accessors" entry): the GENERIC
"any field accessor accepts a predicate argument" mechanism (the FILES
`:on_arrival(:not_none())` example that originally motivated the whole
predicate-argument idea) — `Idchain3` accepting one is a narrow, specific
fix for one function, not a generic dispatch mechanism any OTHER field
accessor gets for free; and the GATE half (a chained sibling function,
e.g. hypothetical `:errors():idchain(:not_none())`) — additive to the
filter behavior, nothing dispatches it yet.

Tests: `tests/references/functions/filters/test_{true,false,none,
not_none,empty,not_empty}_3.py` (one file each, metadata + `check_valid()`
+ `matches()` truth-table), `test_predicate_function_3.py` (base class
raises `NotImplementedError` if a subclass forgets to override
`matches()`), widened `test_idchain_3.py` (new `ARG_TYPES` assertion
plus a `matches()` delegation test), and one live end-to-end test
through a real `ResultsReferenceFinder3`
(`test_errors_with_idchain_not_none_filters_to_entries_that_have_any_source`,
matching compendium 5.36's own worked example exactly — some errors
have a `"source"` field, one does not, `:not_none()` filters to just
the ones that do). `tests/references/` now 1397 passed, up from 1370.

---

## `@variable` registration and `{...}` interpolation evaluation, both halves — BUILT 2026-08-26

Compendium 3.12: "Prior to query, a reference finder can be given
variables that may be used in references. A variable can be any Python
object, but the variable value will be put into a string context so its
`__str__` must make sense... Variable support, including registration, is
a required, must-have capability for RC." Built immediately after the
date/time functions (previous entry) and their path-segment/interpolation
consumption paths — David's own call: "knock out variables now... we have
one use case, interpolation, right at hand," reusing `_resolve_value()`
(the evaluator just built for the function-call half of interpolation) for
the other half it always had a placeholder branch for.

**The key design question, resolved by reading 3.12 literally rather
than assuming**: this is NOT about reaching into a live `CsvPath`
instance's own runtime `variables` dict (`csvpath.py`'s `set_variable()`/
`get_variable()`) — those are scoped to one specific, currently-running
statement, which does not exist at all when a reference is resolved
standalone (v3 is not wired into production yet, see the bucket list's
own "Bigger, standing items"). 3.12's own wording — "a reference finder
can be given variables" — describes something much simpler: explicit,
finder-level registration, done by whoever constructs/uses the finder,
before resolving.

**Built**: `ReferenceFinder3.__init__` gained an optional `variables:
dict | None = None` kwarg (stored as `self._variables`), plus two
post-construction registration methods — `set_variable(name, *,
value)` (mirrors `CsvPath.set_variable()`'s own keyword-only `value`
convention) and `set_variables(dict)` (bulk merge). `_compile_path_
pattern()`/`_resolve_value()` were converted from `@staticmethod` to
ordinary instance methods (every call site already used `self.`-style
calls, so no call site needed to change) so `_resolve_value()` could
reach `self._variables` — its own `Variable3`-part branch, which used
to always raise, now looks the name up and raises only if nothing was
registered for it.

Scoped deliberately narrow, matching David's own framing ("one use
case, interpolation, right at hand"): `@variable` is now usable inside
`{...}` interpolation only. Whether `@variable` should ALSO be usable
as some other function's own direct argument (e.g. a hypothetical
`:uuid(@myvar)`, tied to the separate dual-selector/value-accessor
design item) is untouched, independent follow-up work, not needed to
close this out.

Tests: 6 new cases in `test_reference_finder_3.py`'s `TestResolveValue`
(registered-variable substitution, non-string variable values via
`__str__`, unregistered-variable raises, both registration APIs) plus
one live end-to-end test through a real `FilesReferenceFinder3`
combining a variable AND a clock function in one interpolated string
(`:name("partner-{:year()}-{@company}")`, matching the compendium's
own 5.37 worked example exactly). `tests/references/` now 1370 passed,
up from 1364. Full local-backend suite reconfirmed at the known
11-failure (SFTP/S3/Nos, unrelated) baseline afterward.

---

## "Pure value" date/time functions (5.29), plus their two consumption paths — BUILT 2026-08-26

Found 2026-08-24 (Phase 1 compendium review). The compendium lists eleven
"dumb value-producing functions": `:year()`, `:month()`, `:month_name()`,
`:day()`, `:day_name()`, `:hour()`, `:hour_24()`, `:minute()`, `:second()`,
`:yesterday()`, `:today()`, `:date(...)`. Only `:date()` was registered;
the other ten were not.

**David's own framing, deciding scope**: the ten functions themselves are
simple, so build those first, then dive right into their two real
consumption paths — a `name_one` path segment (e.g.
`$acme.files.orders/:year()` → `acme/orders/2026`) and `{...}` string
interpolation (e.g. `:name("orders-{:year()}.csv")`) — in the same pass,
using the date/time functions themselves as the concrete driving/test
case for both, since "these three chunks of related work... feed off
each other nicely."

**Built, all ten, in a new `csvpath/references/functions/values/`
package** (a new subdirectory — these don't fit `fields/` (manifest/
definition-sourced), `selectors/` (context setters/pointers), or
`well_known_files/`): `Year3`, `Month3`, `MonthName3`, `Day3`,
`DayName3`, `Hour3` (12-hour, 1-12), `Hour243` (24-hour, 0-23),
`Minute3`, `Second3`, `Today3`, `Yesterday3` (the last two as plain
`"YYYY-MM-DD"` strings, matching `:date()`'s own established literal-
date format). All `DATATYPES = (FILES, CSVPATHS, RESULTS)` — genuinely
datatype-independent, computed purely from the clock, no dependency on
any resolved entity/reference state at all.

**New `Function3` mechanism**: a fourth `SOURCE` value, `"clock"`
(`function_3.py`), and a new `compute()` method every clock function
overrides (no args at all, not even `self._arg` — the value comes
purely from the current moment). `DateUtility` (`csvpath/util/
date_util.py`, aliased `daut` per the project's own established utility-
alias convention) is the framework's already-existing single source of
"now" (same one `Metadata.set_time()` already uses) — reused rather than
calling `datetime.now()` directly, and its `OFFSET_DAYS/MONTHS/YEARS`
give every one of these ten a free, deterministic test hook if ever
needed (not used in the tests actually written — see below — which
instead compute their own expected value from `daut.now()` directly, so
they never go stale/flaky regardless of when the suite runs).

**Path-segment consumption, built**: `ReferenceFinder3.
_compile_path_pattern()` (shared by FILES/RESULTS — CSVPATHS has no path
dimension) widened to accept any registered `SOURCE == "clock"` function
as a bare `name_one` path segment (not just `:name("...")` as before),
evaluated via `compute()` and stringified. A non-clock function (e.g. a
field accessor like `:uuid()`) is still rejected there, confirmed by a
regression test — the widening is specifically for clock functions, not
"any function at all."

**`{...}` interpolation consumption, half built**: new shared
`ReferenceFinder3._resolve_value()` — returns a plain literal unchanged,
or evaluates an `InterpolatedString3`'s own parts (literal-text parts
pass through; a `FunctionCall3` part is built and `compute()`'d, only if
its `SOURCE == "clock"`; an `@variable` part still raises, since no
variable-registration API exists yet — see the bucket list's grammar/
argument-type-gaps entry, a separate, bigger prerequisite deliberately
left untouched here). Wired into `_compile_path_pattern()`'s own
`:name("...")` handling, so `:name("orders-{:year()}.csv")` now unwraps
its `{...}` span the same way a plain literal name always has.
`InterpolatedString3`'s own docstring (`reference_3.py`) updated to
reflect this is no longer fully deferred — only the `@variable` half
still is.

Confirmed live for both consumption paths, both datatypes with a path
dimension, before writing formal tests: `$acme.files.orders/:year()`
matched a real `file_home` built from the current year;
`:name("orders-{:year()}.csv")` unwrapped to the same; same for RESULTS'
own `run_home` path matching.

Tests: `tests/references/functions/values/test_*.py` (10 files, one per
function — metadata/`check_valid()` plus a `compute()` test comparing
against `daut.now()` computed independently in the test itself, so nothing
is a stale hard-coded literal); `TestCompilePathPattern`/`TestResolveValue`
in `test_reference_finder_3.py` (the shared-ABC mechanism, both success
and non-clock-function-rejection cases); `TestClockFunctionInPathSegments`
in both `test_files_reference_finder_3.py` and
`test_results_reference_finder_3.py` (end-to-end, real fixtures built
from the actual current year, not a mocked clock). `tests/references/`
now 1364 passed, up from 1305. Full local-backend suite reconfirmed at
the known 11-failure (SFTP/S3/Nos, unrelated) baseline — 2952 passed, 11
failed, no regressions.

---

## Field-accessor fallback to the global ledger entry — BUILT 2026-08-25 (FILES/CSVPATHS), 2026-08-26 (RESULTS/Table 7)

Found 2026-08-25 while starting the deferred global-ledger batch (Tables
2/4/7 of `references_v3_required_manifest_functions.md`). Live-tested
first, not assumed: built a fixture where the global ledger's own entry
for a run said `named_file_name = "LEDGER_VALUE"` and the run's own
manifest said `"RUN_MANIFEST_VALUE"` — both `$*.results.:last():
named_file_name()` and `$acme.results.:last():named_file_name()`
returned the *run's own* value, never the ledger's. Confirmed: no
existing code path read a field directly off a Rule-1a/1b-selected
ledger entry — every field accessor resolved to a real matched entity
and re-read *that entity's own* manifest.json, regardless of how the
entity was found.

**David's design principle, not a one-off workaround**: "when we are
working with any item (registered, loaded, or run) we are talking about
a single conceptual item that owns all its data -- if we have to do more
work to bring all that data together then we do, but that is our
problem, not the user's problem." So the fix is a general fallback: any
field accessor, for any matched entity, checks the entity's own manifest
first and falls back to that same entity's corresponding global-ledger
entry (looked up by uuid) if the field isn't there.

**Built**: `Function3.LEDGER_KEY` (`function_3.py`) — a parallel `{datatype:
dotted key path}` dict, checked only when the entity's own manifest
lookup comes back `None`. New shared ABC helper
`ReferenceFinder3._extract_field_value_with_ledger_fallback()`
(`reference_finder_3.py`), taking a lazy `ledger_entry_getter` callable
so the ledger is only fetched/searched when actually needed. Wired into
`FilesReferenceFinder3`/`CsvpathsReferenceFinder3._extract_data()`
(both match ledger entries by `uuid`, reusing the existing
`_find_manifest_entry_by_uuid` helper). Proven with two real, LEDGER_KEY-
only functions: `:file_manifest()` (FILES, Table 2 — a named-file's own
manifest never self-references its path at all, see issue #261) and
`:group_manifest()` (CSVPATHS, Table 4, same shape). Both have `KEY = {}`
— nothing to find in the entity's own manifest, `LEDGER_KEY` is the only
source. Integration-tested end to end (not just unit-level), including a
"no matching ledger entry" case confirming it falls through to `None`
rather than raising.

**RESULTS/Table 7 — BUILT 2026-08-26.** Table 7 (the Archive Run
Manifest) is per-statement-execution (one entry per csvpath statement
run, keyed by `run_uuid` + `identity`, not a single `uuid`), so it needed
its own matching logic rather than reusing `_find_manifest_entry_by_uuid`
— new `ResultsReferenceFinder3._find_archive_ledger_entry(*, ledger,
run_uuid, identity=None)`. `identity` is optional: confirmed against
`run_registrar.py` that the run-scope fallback fields this was built for
(`archive_name`/`archive_path`/`named_files_root`/`named_paths_root`) are
the same value across every statement in one run, so a run-scope lookup
only needs to match `run_uuid` (first entry found); a caller resolving a
genuinely per-statement field would pass `identity` too. Wired into both
of `ResultsReferenceFinder3._extract_data()`'s field-accessor branches
(run scope via name_one, instance scope via name_three).

A real naming question surfaced along the way and was settled with
David: the doc's suggested mapping (`:archive_name()` → `archive_name`,
`:archive()` → `archive_path`) would have made `:archive()` mean two
different *kinds* of value depending on scope (a bare name at CSVPATHS/
RESULT, a full path at RESULTS run scope) — same shape the `:file()`/
`:file_path()` split resolved earlier this session. **David, 2026-08-26:
keep `:archive()` meaning the name everywhere** (widened its `KEY`/
`LEDGER_KEY`/`POSITIONS` to cover RESULTS run scope via the ledger
fallback, since the run's own manifest never has this field); a new,
separate `:archive_path()` covers the path, `KEY = {}`/`LEDGER_KEY`-only,
matching `:file_manifest()`/`:group_manifest()`'s own shape. Two more new
LEDGER_KEY-only functions built the same way: `:named_files_root()`,
`:named_paths_root()` — genuinely new concepts, no existing function
touched either literal key at all before this. All three new functions
added to `_METADATA_FIELD_FUNCTIONS` (the lesson from the per-entity
batch above, applied this time instead of re-discovered). Tests:
`tests/references/functions/fields/test_archive_path_3.py`,
`test_named_files_root_3.py`, `test_named_paths_root_3.py` (unit), plus
`TestArchiveLedgerFallback` in `test_results_reference_finder_3.py`
(4 integration tests: run-scope fallback success for `:archive()`, all
three ledger-only fields resolving, a no-matching-ledger-entry-gives-
`None` case, and a regression guard proving instance scope still reads
its own manifest directly, untouched by this change). `tests/references/`
now 1179 passed (up from 1166); full suite reconfirmed at the same known
11-failure baseline.

**A second, real bug found and fixed along the way**: `Reference3.
resolve_kind`'s hardcoded `_METADATA_FIELD_FUNCTIONS` tuple did not
recognize *any* of the 19 field-accessor functions built in this whole
session's Phase 2 work (the 17 from the per-entity batch, plus
`file_manifest`/`group_manifest`) — confirmed live, references using them
were silently misclassified as `FIRST_PARTY` instead of `METADATA_FIELD`,
so none of them could actually resolve end to end despite passing their
own isolated unit tests. This is the exact hardcoded-dispatch debt
already flagged in the `resolve_kind` bucket item (still open, see the
bucket list) — fixed for now by adding all 19 names to the existing
tuple (consistent with how every other field accessor is registered
today), not by fixing the underlying mechanism. **Lesson for future
batches: a function's own unit test (metadata + `check_valid()`) does
not prove it actually resolves through a real reference — add at least
one live, end-to-end `resolve()` test per new function, not just
class-level tests.**

---

## `:printouts()` and `:log()` — BUILT 2026-08-26

Found 2026-08-24 (Phase 1 compendium review, item 5.9). The compendium
lists ten well-known file accessors as "the complete class": `:manifest()`,
`:definition()`, `:data()`, `:errors()`, `:printouts()`, `:vars()`,
`:meta()`, `:unmatched()`, `:file(...)`, `:log()`. Checked all ten directly
against the function registry — eight were real; `:printouts()` and `:log()`
had no `Function3` subclass anywhere. Not previously tracked —
`function_coverage_matrix.md` doesn't mention either name, and neither is
on this list's existing "Functions" section of named-but-unbuilt items.

**`:printouts()` built 2026-08-26** — fit the existing per-instance
well-known-file pattern exactly like `:data()`/`:unmatched()`: raw bytes
of `printouts.txt`, same directory level as `data.csv`/`errors.json`
(confirmed against `run_home_maker.py`'s own worked example path),
genuinely optional (`None` if nothing was ever printed). New
`printouts_3.py` (`Printouts3`), registered in the factory, added to
`_METADATA_FILE_FUNCTIONS` (`reference_3.py`) and `_BYTES_ACCESSOR_FILES`
**and** `_ACCESSOR_NAMES` in `ResultsReferenceFinder3` (two separate
whitelists gate this, not one — confirmed live: missing from
`_ACCESSOR_NAMES` alone raised "does not yet support :printouts() as a
name_three function" even after every other piece was wired up). Tests:
`tests/references/functions/well_known_files/test_printouts_3.py` (unit)
plus two integration tests (`test_printouts_resolves_raw_bytes`/
`test_printouts_resolves_none_when_never_written`) in
`TestWellKnownFileAccessors` (`test_results_reference_finder_3.py`).
`tests/references/` now 1184 passed.

**`:log()` built 2026-08-26**, after David added a proper spec for it
(compendium 5.16(b), added directly by him, not this session): a
standalone, not-combinable `name_one` function, legal under any of the
three datatypes but only with `root_major == '*'` (`$*.files.:log()` /
`$*.results.:log()` / `$*.csvpaths.:log()` — datatype is arbitrary since
it is genuinely datatype-independent, just required by the grammar). An
optional int argument gives the last N lines; without it, the whole
file. Resolves to a single string (settled with David: not raw bytes,
not a list of line strings — matches the compendium's own "gives...a
string" framing for text content), `None` if the log file does not
exist yet.

Because this is the first function that is not tied to any datatype/
entity at all, it needed new shared-ABC mechanism rather than reusing
any per-entity pattern: `ReferenceFinder3._log_call_anywhere()` (detects
`:log()` anywhere in `name_one`, for a clear, specific error rather than
a generic one), `_bare_log_call()` (the actual legality check —
standalone, no `name_two`/`name_three`), `_query_log_call()` (called
first thing in each finder's `query()`, before any datatype-specific
dispatch — returns `None` for an ordinary reference, raises for an
illegal combination or a literal `root_major`, otherwise returns the
one-result `ReferenceResults3` pointing at `config.log_file`), and
`_read_log_file()` (the actual read + optional tail, shared by every
finder's `_extract_data()`). New `log_3.py` (`Log3`), registered in the
factory, added to `_METADATA_FILE_FUNCTIONS`. Wired into all three
finders identically (`query()` and `_extract_data()`, four lines each).

Tests: `tests/references/functions/well_known_files/test_log_3.py`
(unit) plus `TestLog` in `test_csvpaths_reference_finder_3.py` (the full
scenario set: bare resolves whole file, int arg tails N lines, missing
file gives `None`, combined-with-a-pointer raises, literal `root_major`
raises) and one confirming end-to-end test each in
`test_files_reference_finder_3.py`/`test_results_reference_finder_3.py`
(proving the shared mechanism composes correctly with each finder's own
`query()` dispatch, not just in isolation). `tests/references/` now 1195
passed, up from 1184.

---

## Field-accessor coverage against real manifest fields — Phase 2 — DONE 2026-08-26

Compendium 5.7: "There must be a field accessor function for every field
available in any of the manifest.json files." David pointed to
`specs/references_v3/spec/references_v3_required_manifest_functions.md`
as the final, authoritative spec for exactly this. Every gap this
section ever tracked is now built — kept in full below for the reasoning
trail.

**First audit (name-matching against the doc's suggested function
names) said 28/82 built.** A second, more rigorous audit (2026-08-25,
introspecting every registered function's actual `KEY` mapping — real
datatype+literal-key pairs — rather than trusting the doc's suggested
names) found the true picture was better than that: several "missing"
names were already covered under a *different* existing name than the
doc suggested (`:origin()` already covers Table 1's `from`/Table 3's
`source_path`, both suggested as `:source()`; `:completed()`/`:valid()`/
`:files_complete()` already have both instance- and run-level keys). Two
real naming collisions were also found and resolved with David:
`:file()` already means something else (an arbitrary RESULTS output
file) — Table 1's `file` field is now `:file_path()` instead, matching
Table 2's own existing name for the same concept; `:status()` is
confirmed fine to reuse across FILES/RESULTS (same mechanism `:uuid()`/
`:home()` already use — one name, per-datatype `KEY`, disambiguated by
the datatype in the reference string itself).

**Built 2026-08-25** (18 new functions, covering all six *per-entity*
tables — 1, 3, 5, 6, 8, 9): `:type()`, `:reference()`, `:file_path()`
(Table 1); `:archive()`, `:group_file()`, `:named_paths()` (Table 3);
`:error_count()`, `:named_paths_uuid()`, `:named_file_uuid()`,
`:named_file_path()`, `:named_file_size()`, `:named_file_last_change()`,
`:named_file_fingerprint()` (Table 5); `:run_dir()`, `:instance_index()`
(Table 6, `:archive()`/`:named_paths_uuid()` above also cover this
table's own scope); `:named_paths_group()`, `:run_method()` (Table 8).
All registered, tested (`tests/references/functions/fields/test_*.py`,
one file each), full `tests/references/` suite passing (1150) after.

**Built 2026-08-25, second pass** — the ledger-fallback mechanism (see
its own entry above) plus two real Table 2/4 functions that needed it:
`:file_manifest()`, `:group_manifest()`. Also fixed along the way:
`resolve_kind`'s hardcoded dispatch tuple didn't recognize *any* of the
19 functions from the first pass, so none of them actually resolved end
to end despite passing their own unit tests — added all 19 names, and
added the missing integration tests. `tests/references/` now 1166
passed, full suite 2754 passed.

**`:template()` — BUILT 2026-08-26.** The `results_registrar.py` schema
gap this bullet used to cite turned out to already be fixed (confirmed
live: both `results_registrar.py`/`run_registrar.py` already write a
`template` field, unconditionally) — only the position-based-dispatch
mechanism itself needed designing/building, not a data-availability
blocker.

Settled with David: one function, dual source, via a new
`Function3.BARE_SOURCE` attribute (`function_3.py`) — `Template3` sets
`SOURCE = "manifest"` (used when a real pointer/matched version is
present — reads that version's own historical manifest snapshot,
Table 1/Table 3) and `BARE_SOURCE = "definition"` (used bare, no
pointer/match at all — reads the entity's CURRENT default from
definition.json, Table 8/Table 9). Same `KEY` string ("template")
works for both, since it is genuinely the same literal field, just
captured at different moments — matches Table 9's own doc note that
its `template` is "the actual source of truth... the Named-Paths
Manifest's own template field is a snapshot of whatever this held at
that particular load."

FILES needed no new runtime check at all — its two existing code paths
(`_bare_definition_field_call()`'s bare-name_one shape vs. the ordinary
name_three-with-a-real-match shape) already structurally correspond to
"no version selected" vs. "a version was selected," so widening
`_bare_definition_field_call()` to also accept `BARE_SOURCE ==
"definition"` was the only change needed there. CSVPATHS is different —
both cases go through the SAME code path (a pointer and the field
accessor coexist in one combined `name_one` chain), so it genuinely
needed a new shared ABC helper, `ReferenceFinder3._pointer_present()`,
to check whether a real `:first()`/`:last()`/`:index()` rode alongside
`:template()` in that chain and pick the resource accordingly. RESULTS
needed no special-casing at all — a run is not a versioned, editable
config artifact the way a named-file/named-paths registration is, so
`:template()` there is just an ordinary `SOURCE == "manifest"` field
with a `LEDGER_KEY` fallback to Table 7, identical in shape to every
other RESULTS run-scope field built this session.

Confirmed live (not just via tests) for all three datatypes before
writing the formal tests: CSVPATHS `:first():template()`/
`:last():template()` gave each matched version's own snapshot while
bare `:template()` gave the pooled current default for every version;
same for FILES; RESULTS gave the run's own value directly.

Also found along the way: Table 5's own doc field list is missing a
row for `template` entirely, even though `results_registrar.py`
genuinely writes it — a real doc gap, not fixed here (David's file),
built from the confirmed code rather than the doc. Still worth David
adding the row at some point.

Tests: `tests/references/functions/fields/test_template_3.py` (unit),
`TestTemplateBareVsPointerDualSource` (CSVPATHS),
`TestTemplateBareVsMatchedDualSource` (FILES), and
`test_template_at_run_scope` in RESULTS' own
`TestFieldAccessorFunctions`. `tests/references/` now 1305 passed, up
from 1293.

**`sources`/`destinations`/`transfers`/`scripts`/`webhooks` sub-field
accessors (Table 8/9) — BUILT 2026-08-26.** Confirmed against the real
dataclasses (`paths_descriptor.py`/`file_descriptor.py`) before
building, not the doc alone: `sources.<name>.*`/`destinations.<name>.*`/
`transfers.<name>.on_complete_*` are genuinely keyed by an arbitrary
name (`dict[str, ...]`); `scripts.on_complete_*`/`webhooks.on_complete_*`
are fixed four-state objects with no name dimension at all — the doc's
`(str)` on two of the four scripts accessors was a leftover copy-paste
artifact, dropped (all eight built zero-arg). The name-keyed group
needed a genuinely new mechanism: `Function3.KEY` can now hold a `"{}"`
placeholder (e.g. `"sources.{}.port"`), filled with the field accessor's
own arg via new shared `ReferenceFinder3._apply_key_arg()` before the
ordinary dotted-path walk — the first field accessors whose KEY needed
a per-call value, not just a per-datatype one.
`FilesReferenceFinder3._bare_definition_field_call()` also had to be
relaxed to accept an argument-bearing call (previously argument-less
only). 20 new functions: `source_address/port/username/password`
(FILES), `destination_address/port/username/password` (CSVPATHS),
`transfer_on_complete_all/valid/invalid/error` (CSVPATHS, keyed by
csvpath statement identity), `script_on_complete_all/valid/invalid/
error` and `webhooks_on_complete_all/valid/invalid/error` (CSVPATHS,
zero-arg). `tests/references/` now 1284 passed.

**Most of Tables 2/4's remaining fields — BUILT 2026-08-26.** Table 7
was already done (see its own entry above) — every field except
deprecated `base_path` (issue #225) and `:template()` (above) is
covered. Cross-referenced every Table 2/4 field against Tables 1/3's
own fields before building anything: most turned out to already be
fully covered by an existing per-entity `KEY` that always succeeds (no
`LEDGER_KEY` ever needed, since the field is never actually missing
from the entity's own manifest) — `time`/`uuid`/`type`/`fingerprint`/
`origin`(`from`/`source_path`)/`named_paths_name`/`home`
(`named_paths_home`)/`group_file`/`file_manifest`/`group_manifest` all
fell into this bucket, needing no code change at all. The GENUINE gaps
were `username`/`hostname`/`ip_address` — confirmed against
`file_registrar.py`/`paths_registrar.py` that neither Table 1 nor Table
3 has these fields at all, only the global arrivals/loads ledgers
(Tables 2/4) do (RESULTS already had them directly, unaffected).
Widened the existing `Username3`/`Hostname3` to also cover FILES/
CSVPATHS via `LEDGER_KEY` (their own `KEY` has no FILES/CSVPATHS entry
at all — same "nothing to find in the entity's own manifest" shape as
`:file_manifest()`). Built one new function, `Host3`/`:host()`, for
`ip_address` (FILES/CSVPATHS only — RESULTS' own `ip_address` is
explicitly deprecated, "Do not use," no function at all).

**A real naming question surfaced and was settled with David
(2026-08-26)**: the doc's Table 5 row for the `hostname` field said
`:host()`, not `:hostname()` — but `:hostname()` already existed,
tested, KEY=`RESULTS:"hostname"`. Since Tables 2/4/5's `ip_address` rows
*also* say `:host()`, and `hostname`/`ip_address` are adjacent rows in
all three tables, this was almost certainly the same copy-paste-
artifact pattern as the webhooks/transfers/destinations doc bugs found
earlier — confirmed with David: keep `:hostname()` as-is, `:host()` is
a separate, new function for `ip_address` only, not a rename/merge.

Tests: `tests/references/functions/fields/test_host_3.py` (unit),
widened `test_username_3.py`/`test_hostname_3.py`, plus
`TestUsernameHostnameHostLedgerFallback`
(`test_files_reference_finder_3.py`) and two new tests in CSVPATHS'
`TestFieldAccessorFunctions` (`test_csvpaths_reference_finder_3.py`).
`tests/references/` now 1293 passed, up from 1284.

---

## Corrections needed in the `:manifest()`/`:definition()` compendium section — CONFIRMED FIXED

Originally found while reviewing David's own replacement text for the
"root `:manifest()` and `:definition()` files" section:

- `$acme.files.:manifest():last()` was given as an example returning "the
  last file registration data captured in the **global** files ledger
  manifest" — wrong on two counts (a literal root_major can never mean
  the global ledger; even read as "acme's own manifest, last entry," that
  shape doesn't work today either, see the separate, still-open
  `$name.files.:manifest():last()` bucket item).
- The draft called the definition-file function `:description()`; the
  real, existing function is `:definition()`.

**Confirmed fixed 2026-08-26** by reading the current compendium text
directly (5.12): it now reads `$*.files.:manifest():last()` (with the
`*`), and `:description()` doesn't appear anywhere in the document
anymore. David corrected his own draft since this was originally found.

---

## `'*'` traversal — RESULTS/CSVPATHS: two now-fixed sub-items

(Split out of the still-open "`'*'` traversal — RESULTS/CSVPATHS
remaining gap" bucket-list entry, which still has open items of its
own — see that entry for `:groups()`/RESULTS `:having()`.)

- ~~`:manifest()` combined with real `'*'`-traversal narrowing~~ — **FIXED
  2026-08-26**, both `ResultsReferenceFinder3` and `CsvpathsReferenceFinder3`.
  `_star_run_selector_chain()` (RESULTS) and the equivalent `non_pointers`
  guard in `_query_star_traversal()` (CSVPATHS) now exempt `:manifest()` the
  same way `:all()`/`:flatten()`/`:having()`/a field accessor already were.
  `_extract_data()`'s Star3 branch in both finders now disambiguates a
  Rule-1a/1b global-ledger result from a genuine traversal-selected result by
  comparing `result.path` against the ledger's own known, fixed path
  (`Nos(archive/inputs_csvpaths_path).join("manifest.json")`) instead of the
  now-ambiguous `result.uuid is not None` check (both shapes carry a real
  uuid once this composes with real narrowing) — path equality means Rule
  1a/1b (read the global ledger, keyed by uuid or not per Rule 1a vs 1b);
  anything else falls through to the pre-existing per-entity manifest read.
  For CSVPATHS specifically, note a plain bare pointer + bare `:manifest()`
  (e.g. `:last():manifest()`) is ALWAYS the exact two-function shape
  `_pointer_before_manifest()` matches and is intercepted as Rule 1b before
  ever reaching `_query_star_traversal` at all, regardless of root_major
  being `'*'` — so there is no "FLATTEN mode + manifest via genuine
  traversal" case for CSVPATHS, only GROUP mode (`:all():manifest()`) or a
  field-accessor riding alongside it reach the new exemption. Tests: RESULTS
  `TestScopeLimits::test_manifest_combined_with_traversal_now_works`;
  CSVPATHS `TestStarTraversalGroup::
  test_all_with_last_and_manifest_gives_each_groups_own_manifest_entry` and
  `TestStarTraversalFieldAccessor::
  test_field_accessor_combined_with_manifest_now_also_works`. Full
  `tests/references/` suite (1166 tests, all green) and full local-backend
  suite (2754 passed, 11 failed) both confirmed after this fix — the 11
  failures are the same known SFTP/S3/Nos baseline, unrelated. See
  `references_v3_compendium.md` §6 for the full writeup.
- ~~`CsvpathsReferenceFinder3`'s own `'*'` traversal still requires a
  pointer in POOL/flatten mode~~ — **CORRECTION, 2026-08-23: this was
  already fixed, the entry was stale the moment it was added.** Added
  2026-08-22 from a snapshot of the old compendium copy (dated as of
  2026-08-19) that turned out to predate a same-day fix. Confirmed live
  against current code (`csvpaths_reference_finder_3.py:381-423`): the
  POOL/flatten branch now has `if pointers: ... else: selected_versions =
  pooled` exactly mirroring the GROUP/`:all()` branch — a missing pointer
  returns every candidate unreduced in both modes. `references_v3_
  expressions.md`'s own "Status notes" section confirms this directly:
  "CSVPATHS' OWN POINTER-OPTIONALITY GAP CLOSED TOO, 2026-08-19... This
  closes out star-traversal pointer-optionality across all three
  datatypes cleanly." Lesson: even a same-day-dated snapshot doc can be
  stale relative to the actual final code state — verify live, not just
  against the most recent-looking doc.
