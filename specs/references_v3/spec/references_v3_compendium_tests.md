# References v3 Compendium — Test Conformance Map

Maps each numbered item in `references_v3_compendium.md` (`#### N.M`
headings) to the test(s) that verify it. Originally built during Phase 1
of `specs/references_v3/notes/rc_roadmap.md` (2026-08-24/25); this is the
Phase 3 "full internal consistency pass" regeneration.

**Conventions (unchanged from the original):**
- One `#### N.M` heading per compendium item, in the same order as the
  compendium itself.
- Below each, a bullet list of `test_file.py::TestClass::test_method`
  references that verify it. Many-to-many is normal and expected.
- An item with no test yet is marked explicitly, `- *(no test yet)*` —
  never left silently blank.
- Doc-pointer/conceptual-framing items (no independent behavioral claim)
  are marked `- Doc pointer only, not independently testable.`

**2026-10-18 regeneration note:** the compendium's own section numbering
has shifted substantially since the 2026-08-24 original — a brand new
section 4 ("Wildcards") was inserted, section 3 ("The Reference Model")
gained many new lettered sub-items (3.7a-c, 3.9a-d, 3.12a, 3.19b), and
section 5/old-"Functions" (now section 6) roughly doubled in size with
new content on time-component functions (6.27-6.27g), direction/ordinal
functions (6.22-6.31), and the predicate-argument GATE mechanism
(6.35-6.41) — almost all of it built in the two weeks immediately
preceding this regeneration. The clean mapping is: old 2→new 2
(unchanged), old 3→new 3 (expanded in place), **new 4 inserted**, old
4→new 5 (unchanged, same 23 items), old 5→new 6 (expanded, 44→48 items),
old 6→new 7 (unchanged, same 9 items). Every "no test yet" marker from
the original pass was re-checked against current code; the overwhelming
majority turned out to be built and tested since — this regeneration
updates them rather than leaving them stale. Verification method: full
re-read of the current compendium end to end, cross-referenced against
this session's own direct, verified engineering history (PRs building
the direction/time-component/GATE/taxonomy mechanisms were built, live-
tested, and full-suite-verified in the days immediately before this
pass — not reasoned from memory) plus targeted grep/read confirmation
of test file existence and content for everything else. Given the
volume (~180 items), this was not re-executed as 180 individual live
Python snippets from scratch — treat citations for mechanisms NOT built
in the immediately-preceding session days as grep/read-confirmed (test
file and relevant class/method exist, content read to confirm it
exercises the claim) rather than freshly re-run end to end. Anything
genuinely uncertain is marked below rather than guessed.

---

## 2. Overall usage pattern

#### 2.1
- Exercised implicitly across all of `tests/references/` (every finder
  test follows parse → construct finder → `query()`/`resolve()`) — no
  single test isolates the workflow shape itself, and it doesn't need one.

#### 2.2
- `test_reference_expression_3.py::TestReferenceExpression3Construction`
  (op must be one of `UNION`/`SUBTRACT`/`INTERSECT`)

#### 2.3
- Doc pointer only, not independently testable.

## 3. The Reference Model

#### 3.1
- Doc pointer only, not independently testable.

#### 3.2
- `test_references_3_grammar.py`, `test_reference_parser_3.py::TestConstruction`

#### 3.3
- *(no test yet — `#name_two` is not built anywhere yet, including for
  FILES; see bucket list "`#name_two` combined with `'*'` traversal —
  still not supported" entry. Confirmed still accurate: `Reference3`'s
  own `name_two` field exists structurally but no finder resolves a
  worksheet via it.)*

#### 3.4
- Doc pointer only, not independently testable.

#### 3.5
- `test_references_3_grammar.py`, `test_reference_3.py::TestFunctionCall3`
  (argument-kind parsing: string/int/function/regex/variable, all five)

#### 3.6
- **UPDATED from "no test yet" (was marked not built 2026-08-24) —
  `@variable` is now fully built.** `test_reference_parser_3.py` and
  `test_reference_finder_3.py` both exercise `set_variable()`/
  `set_variables()`/`variables()`, confirmed by grep (variable-setting
  methods are tested in both files) and by this session's own extensive
  use of `variables={...}` fixtures throughout `test_results_reference_
  finder_3.py`/`test_csvpaths_reference_finder_3.py` (e.g. `:having(
  @identities)`, built and tested this week).

#### 3.7a
- Same as 3.6 — both usages (string interpolation, function arguments)
  confirmed built and tested.

#### 3.7b
- `test_reference_3.py::TestInterpolatedString3`,
  `test_reference_transformer_3.py::TestStringInterpolation`,
  `test_reference_parser_3.py::TestStringInterpolationThroughParser`
  (the `{@variable}` form specifically)

#### 3.7c
- `test_reference_parser_3.py`/`test_reference_finder_3.py` (the three
  methods' own construction/usage, confirmed present and exercised)

#### 3.8
- `test_reference_3.py::TestReference3` (root_major parsing/round-trip,
  string/`*`/`:name()`/`:regex()` forms)

#### 3.9
- `test_csvpaths_reference_finder_3.py` (version-selecting name_one,
  exercised throughout); `test_files_reference_finder_3.py`/
  `test_results_reference_finder_3.py` (file-home/run-dir path semantics)

#### 3.9a
- *(no dedicated test found for the literal "name_one cannot be empty /
  reference cannot end on a bare `.`" grammar constraint — likely
  enforced structurally by the grammar itself the same way 7.1's "LALR
  works" claim is, but not confirmed by a specific test. Worth a
  targeted grammar test if this is considered RC-blocking; low risk
  since a malformed reference of this shape would fail to parse at all,
  loudly, not silently misbehave.)*

#### 3.9b
- *(no dedicated test found for the specific "name_one cannot start
  with `/` or end with `/`" constraint shown in the three-reference
  example. Same risk profile as 3.9a — likely a grammar-level rejection,
  not independently verified by name.)*

#### 3.9c
- `test_files_reference_finder_3.py` (`_apply_implied_star()`'s own test
  coverage via `TestTypeGate`'s bare/explicit-`*` equivalence tests,
  built this week, plus the pre-existing implied-star tests for other
  bare functions); `test_results_reference_finder_3.py`/
  `test_csvpaths_reference_finder_3.py` (`:all()`/`:flatten()`/
  `:groups()` as wildcards, `:manifest()`/`:definition()`/`:on_arrival()`/
  `:fingerprint()` as non-path-segment exemptions — all exercised
  throughout each finder's own test suite)

#### 3.9d
- `test_files_reference_finder_3.py::TestTypeGate::test_explicit_star_gate_is_the_same_mechanism`,
  `test_prefixed_explicit_star_gate_is_the_same_mechanism` (the EXACT
  two worked-example pairs cited here, built and confirmed live this
  week, closing what was previously the last open compendium 3.9d gap)

#### 3.10
- Doc pointer only, not independently testable (explanatory framing for
  3.11/6.27's own time-function mechanics, tested there).

#### 3.11
- *(no test yet for this exact two-reference comparison — the
  underlying mechanisms (`:yesterday()` as context, `:flatten()`/
  `name_three` vs `name_one` termination) are each separately tested,
  but no single test exercises this specific "same intent, different
  termination point" pair side by side. Low risk — both halves are
  independently well-tested.)*

#### 3.12
- `test_files_reference_finder_3.py`/`test_results_reference_finder_3.py`
  (template-level path matching, 0/1/2-level fixtures throughout)

#### 3.12a
- Same template-level fixtures as 3.12 — 0-level/1-level/2-level cases
  are all exercised, though not against this exact literal example path.

#### 3.13
- `test_files_reference_finder_3.py::TestBareFunctionOnlyNameOne`-style
  zero-level tests, `test_results_reference_finder_3.py` equivalent
  zero-level run tests

#### 3.14
- Covered piecemeal by the same template-level + `:name()`/`:flatten()`/
  `:regex()` tests as 3.12 — not against this exact literal example set.

#### 3.15
- `test_csvpaths_reference_finder_3.py` (version-selecting name_one,
  manifest-array-only versioning, exercised throughout)

#### 3.16
- `test_csvpaths_reference_finder_3.py::TestVersionPointer` (single-
  version-at-a-time retrieval); `test_results_reference_finder_3.py`
  (the `errors.json` single-file-at-a-time analog)

#### 3.17
- `test_csvpaths_reference_finder_3.py::TestVersionPointer` (identical
  `group_file_path` across versions, differentiated by `uuid`)

#### 3.18
- `test_csvpaths_reference_finder_3.py::TestVersionPointer`,
  `TestVersionRange`, `TestVersionDirectionFunctions` (the `:last()`/`*`/
  `:date():after():first()` shapes, though not against this exact
  three-version UUID fixture literally)

#### 3.19
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` (name_three string/function/`*`
  forms, exercised throughout)

#### 3.19b
- `test_files_reference_finder_3.py`/`test_results_reference_finder_3.py`
  (implied-`*` for a functions-only name_three — the compendium 4.2b/
  functions-only-implies-star fix built earlier this session)

#### 3.20
- `test_files_reference_finder_3.py` (`:name("orders.csv").:last()`
  shape); `test_csvpaths_reference_finder_3.py` (`:after("...")` on
  name_three). *(No test for the third example — `:groups()/:from(
  :index(-2)):to(:index(-1)).header_checks:error_count()` is a compound
  shape combining `:groups()`+`'*'`+range+name_three+`:error_count()`
  all at once; each piece is separately tested but not this exact
  combination.)*

#### 3.21
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` (the structure-table's own
  per-datatype name_one/name_three return shapes, exercised end to end)

## 4. Wildcards

#### 4.1
- `test_files_reference_finder_3.py::TestStarFlattensAcrossAllFiles`/
  `test_results_reference_finder_3.py` bare-`*` pooling tests

#### 4.2
- `test_files_reference_finder_3.py::TestAllGrouping`,
  `TestAllGroupingAtAMiddlePosition`; `test_results_reference_finder_3.py`
  equivalent `:all()` grouping tests — per-group independent `:last()`
  reduction, confirmed

#### 4.2b
- `test_files_reference_finder_3.py`/`test_results_reference_finder_3.py`/
  `test_csvpaths_reference_finder_3.py` (the "at most one `:all()`/
  `:groups()`" rejection tests, the three degenerate-to-`*` cases, and
  `name_three`'s own `:all()`-only/no-`:groups()` restriction, all
  exercised across the three finders' own position-enforcement tests)

#### 4.3a
- Covered by the degenerate-case tests under 4.2b (RESULTS `name_three`
  `:all()`≡`*`) — not against the `print-mode:separate`/`parquet()`
  rationale text itself, which is explanatory, not independently
  testable.

#### 4.3b
- `test_files_reference_finder_3.py`/`test_results_reference_finder_3.py`
  (illegal double-grouping-marker rejection, built this week for
  `:groups()`+`:all()` specifically, pre-existing for `:groups()`+
  `:groups()`/`:all()`+`:all()`)

#### 4.3c
- `test_files_reference_finder_3.py::TestStarTraversalPathNarrowingAndNameThree::test_prefixed_flatten_pools_any_depth_beyond_prefix_across_groups`-
  style tests (prefix-then-flatten vs. bare-flatten distinction,
  exercised for both FILES and RESULTS)

#### 4.3d
- *(no test yet found for the specific "`:flatten()/*` is illegal"
  rejection — `_apply_implied_star()`'s own exemption list treats
  `:flatten()` as already-a-wildcard, but no test asserts a trailing
  `*` after it is rejected as contradictory. Worth a small, cheap
  regression test.)*

#### 4.3e
- Confirmed structurally: `:flatten()` has no `name_three` dispatch
  branch in any finder — exercised negatively by `name_three`'s own
  position-enforcement tests (4.2b) rejecting it there.

#### 4.4
- `test_files_reference_finder_3.py::TestStarFlattensAcrossAllFiles`
  (the alpha/beta/cappa-style worked example, matching the compendium's
  own EXAMPLE SCENARIO in spirit, not this exact literal fixture)

#### 4.5
- Covered piecemeal by 4.2b/4.3b/4.3d's own legal/illegal combination
  tests — not against this exact "unlikely but legal" example set.

## 5. Query vs. Resolve

#### 5.1
- Path/uuid/identity: exercised throughout. The `identity` field doing
  double duty for worksheet name (files) is *still not built* for the
  worksheet case — same as 3.3.

#### 5.2
- *(no test yet — the "reference expression may combine two references
  without further resolution" query()-only mode does not exist as a
  distinct capability; `ReferenceExpression3` always resolves both
  sides fully today (`_resolve_side()` always calls `.resolve()`, never
  a query()-only path) — confirmed by reading `reference_expression_3.py`
  directly this pass. See bucket list for whether this is still wanted
  as a distinct mode or whether always-resolving is now the accepted
  design.)*

#### 5.3
- **UPDATED from "no test yet, single most consequential gap" (2026-08-24)
  — now substantially built.** The query()-always-succeeds / resolve()-
  raises-on-multi-match split is implemented via the `ambiguous_content_
  read` flag pattern, confirmed built and tested across all three
  finders (`deferred_work_done_list.md`'s own "'*'-traversal content-
  accessor guards" entry, partition-aware fix completed 2026-10-16) —
  `test_files_reference_finder_3.py`/`test_results_reference_finder_3.py`/
  `test_csvpaths_reference_finder_3.py` all have dedicated tests
  asserting `query()` returns multiple flagged results while `resolve()`
  raises. Not verified as 100% exhaustive across every possible shape,
  but the general mechanism is real and tested, not just the literal-
  root case this item's original note implied was the only gap.

#### 5.4
- **UPDATED from "no test for markdown rendering" (2026-08-24) — now
  built.** `csvpath/references/function_describer_3.py`'s own
  `describe()`/`describe_all()` produce real markdown (confirmed by
  reading the module directly this pass — it is "deliberately just a
  markdown-string producer," per its own comment). `test_function_
  describer_3.py` exercises it.

#### 5.5
- Tangental cross-reference to 3.9c's own `:manifest()` rule — not an
  independent claim.

#### 5.6
- `test_files_reference_finder_3.py::TestGlobalArrivalsLedger`,
  `test_results_reference_finder_3.py::TestGlobalArchiveLedger`,
  `test_csvpaths_reference_finder_3.py::TestGlobalLoadsLedger` (Rule 1a)

#### 5.7
- Same `TestGlobalArrivalsLedger`-family tests — `uuid=None` for
  multiple, real uuid for one ordinal-selected entry (Rule 1a/1b)

#### 5.8
- `test_results_reference_finder_3.py` (ledger record vs. instance-file
  distinction, both sides separately covered)

#### 5.9
- `test_files_reference_finder_3.py::test_star_with_definition_is_still_not_supported`
  and CSVPATHS/RESULTS equivalents

#### 5.10
- `test_results_reference_finder_3.py` (bare pointer resolve → `None`)

#### 5.11
- Exercised throughout the three finders' own name_one-terminal
  `query()` tests.

#### 5.12
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` (name_one-terminal path
  assertions, one per datatype row)

#### 5.13
- Same three files' name_three-terminal `query()` tests

#### 5.14
- `test_reference_3.py::TestResolveKind` (all three `resolve_kind`
  values)

#### 5.15
- `test_reference_3.py::TestResolveKind::test_first_party_when_no_name_three_and_no_name_one_functions`,
  `test_first_party_for_ordinary_selector_function_with_nested_arg`

#### 5.16
- `test_reference_3.py::TestResolveKind::test_metadata_file_for_plain_well_known_file_function`

#### 5.17
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` `:manifest()`/`:definition()`
  content tests

#### 5.18
- `test_reference_3.py::TestResolveKind::test_metadata_field_when_value_locator_nested_in_terminal_function`

#### 5.19
- `test_results_reference_finder_3.py::test_errors_with_idchain_filters_to_matching_source`,
  `test_errors_with_idchain_no_match_returns_empty_list`,
  `test_errors_with_idchain_regex_filters_by_search_not_full_match` (the
  three *filter* examples). **UPDATED: the two *gate* examples
  (`:errors():idchain(...)` chained after) are now built** — the
  predicate-argument GATE mechanism (`field_call`/`_matches_field_
  predicate`) built 2026-10-17/18 generalizes to exactly this shape;
  confirmed via `TestErrorsIdchainGate`/`TestErrorsCountGate` in
  `test_results_reference_finder_3.py`.

#### 5.20
- Same as 5.19 — explanatory note for the same worked example.

#### 5.21
- `test_normative_examples_results.py`/`files`/`csvpaths` (resolve
  matrix cells, exercised end to end per datatype)

#### 5.22
- `test_reference_finder_3.py` (`resolve_from()` with an explicit
  `:uuid(...)` selection), `test_files_reference_finder_3.py::TestBareUuidLookup`/
  `test_csvpaths_reference_finder_3.py::TestBareUuidLookup` (built this
  week, the exact bare-selector mechanism this note describes)

#### 5.23
- `test_files_reference_finder_3.py::TestStarFlattensAcrossAllFiles`
  (the exact reference used in this pseudocode example)

## 6. Functions

#### 6.1
- `test_references_3_grammar.py`, `test_reference_3.py::TestFunctionCall3`
  (form/argument-count parsing); order-independence is structural (AND
  combination, not sequence-sensitive) — exercised implicitly throughout,
  no single dedicated "order doesn't matter" test.

#### 6.2
- `test_reference_3.py::TestFunctionCall3`, `TestVariable3`, `TestRegex3`
  (one test family per argument kind — string/int/variable/function/regex,
  all five now covered per 3.6's update)

#### 6.3
- `functions/test_reference_function_factory_3.py` (name-keyed registry
  lookup, exercised via every function's own construction test)

#### 6.4
- `test_function_describer_3.py` — see 5.4's own update (markdown
  rendering is built, not just the structured-`describe()` dict).

#### 6.5
- `test_reference_3.py::TestResolveKind` (the role/category split,
  exercised via `ROLE`/`SOURCE` class attributes throughout every
  function's own test file)

#### 6.6
- `test_reference_expression_3.py::TestUnion` (UNION compatibility by
  function KIND, e.g. `:named_paths_name()`/`:named_results_name()`
  comparable, `:named_file_name()`/`:fingerprint()` not)

#### 6.7
- `test_function_describer_3.py` (`SELECTOR_WHEN_ARGUED` row rendering);
  every `KIND`-declaring function's own unit test (`test_uuid_3.py`,
  `test_named_file_uuid_3.py`, `test_named_paths_uuid_3.py`,
  `test_named_paths_name_3.py`, `test_named_results_name_3.py`,
  `test_named_file_name_3.py`, `test_fingerprint_3.py`,
  `test_named_file_fingerprint_3.py`, `test_named_paths_fingerprint_3.py`,
  `test_type_3.py`) — this entire taxonomy's retrieve/select duality was
  closed across PRs this week (all 10 named functions now covered); see
  `deferred_work_done_list.md`'s own "functional taxonomy" entries.

#### 6.8
- *(no test yet for these EXACT literal worked examples — the
  underlying mechanisms (bare `:manifest():uuid()` mapping, UNION/
  SUBTRACT/INTERSECT by uuid across datatypes) are each separately
  tested — `test_reference_expression_3.py::TestPathsVsValuesEndToEnd::
  test_intersect_files_paths_left_results_values_right_is_genuinely_cross_datatype`
  is the closest real analog (confirmed live this week, closing what
  the bucket list used to call "cross-datatype uuid + set operations,
  still fully open") — but no test runs this section's own literal
  four examples verbatim.)*

#### 6.9
- Doc pointer only (explanatory elaboration on 3.16/6.47's own "one
  file at a time" rule) — not independently testable beyond those.

#### 6.10
- Doc pointer/aspirational completeness goal, not independently
  testable as a single claim — see `function_coverage_matrix.md` for
  the actual per-field audit (referenced directly by 6.11).

#### 6.11
- Doc pointer only — `specs/references_v3/notes/function_coverage_matrix.md`
  is the living artifact this item points to, not itself asserting a
  pass/fail state here. (Not independently re-audited for currency in
  this pass — it is a separate document with its own maintenance
  cadence, out of scope for this regeneration.)

#### 6.12
- `tests/references/functions/well_known_files/` (one test file per
  built file accessor — `:manifest()`, `:definition()`, `:data()`,
  `:errors()`, `:vars()`, `:meta()`, `:unmatched()`, `:file()`,
  `:log()`, `:readme()`, `:printouts()` all present and tested there)

#### 6.13
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` (manifest shape per schema,
  exercised via real fixture data throughout)

#### 6.14
- `functions/well_known_files/test_manifest_3.py`,
  `test_files_reference_finder_3.py::TestManifestCombinedWithNameThree`
  (all three context-aware resolutions)

#### 6.15
- Same as 6.14 — the three literal examples given here are each
  structurally covered, not verified against this exact literal text.

#### 6.16
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` (manifest existence per entity
  level, exercised throughout)

#### 6.17
- `functions/well_known_files/test_definition_3.py` (optional/absent
  `definition.json` handling)

#### 6.18
- `test_files_reference_finder_3.py::TestGlobalArrivalsLedger` (bare
  `:manifest()` at `'*'`), `TestGlobalArrivalsLedgerOrdinalIndexing`

#### 6.19
- `functions/fields/test_fingerprint_3.py`,
  `test_files_reference_finder_3.py::TestBareFingerprintLookup` (the
  bare-vs-`:manifest()`-prefixed equivalence pairs); `functions/fields/
  test_on_arrival_3.py` (the `:definition():on_arrival(...)` examples)

#### 6.20
- Exercised implicitly wherever a finder test covers a missing/absent
  manifest or definition file — no single test isolates all three
  listed cases together.

#### 6.21
- `functions/well_known_files/test_log_3.py` (optional int-arg line
  count, confirmed `test_int_arg_is_valid`/`test_string_arg_is_rejected`)

#### 6.22
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` (all seven ordinal functions'
  own range/pointer tests, including `:before()`/`:after()` built
  2026-10-16 — see `deferred_work_done_list.md`'s "Direction/ordinal
  functions" entry)

#### 6.23
- `test_reference_finder_3.py` (`_apply_range`/index-counting behavior)

#### 6.24
- Date-mode `:from()`/`:to()`/`:before()`/`:after()` tests across all
  three finders (arrival/load/run date filtering, per-datatype)

#### 6.25
- `test_csvpaths_reference_finder_3.py` (statement-range tests —
  index-mode only, date-mode explicitly rejected there, confirming
  this exact "no time element" claim)

#### 6.26
- No direct test — conceptual Anchor/Direction/Stepping framework,
  demonstrated by 6.28-6.31's own examples.

#### 6.27
- `functions/values/` time-component function test files
  (`test_year_3.py`, `test_month_3.py`, `test_day_3.py`, `test_hour_3.py`,
  `test_hour_24_3.py`, `test_minute_3.py`, `test_second_3.py`,
  `test_yesterday_3.py`, `test_today_3.py`, `test_now_3.py`,
  `functions/selectors/test_date_3.py`) — all 13 functions built, per
  `deferred_work_done_list.md`'s "Time component functions acting as
  context setters — BUILT 2026-10-17" entry (was 1/11 built at the
  2026-08-24 original pass; now complete).

#### 6.27b
- Covered by the same time-component test files as 6.27 — the
  "first moment of that period" interpretation is the core behavior
  those tests assert.

#### 6.27c
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` (bare time-component-as-context
  vs. nested-as-anchor tests, both shapes exercised)

#### 6.27d
- `test_files_reference_finder_3.py::test_yesterday_as_context`-style
  tests (context form); range-anchor and string-interpolation forms
  each covered by their own respective mechanism's tests (6.27c, 3.7b)
  — not against this exact three-example set verbatim.

#### 6.27e
- Same time-component tests as 6.27/6.27c — all three usage shapes
  (range, pointer-context, directional anchor) exercised.

#### 6.27f
- Covered by the same date-range comparison tests — the datetime-vs-
  string-slicing rewrite (flagged explicitly in memory: "a first draft
  would have let `:hour()`/`:minute()`/`:second()` silently collapse to
  `:today()`'s own meaning... corrected after real `datetime` parsing
  was required") confirms this exact precision concern was tested and
  fixed, not just assumed.

#### 6.27g
- `functions/values/test_now_3.py`, `test_yesterday_3.py` (the four
  listed behaviors — range/anchor/interpolation/relative-to-a-given-
  datetime — all exercised across these and the shared date-range
  mechanism's own tests)

#### 6.28
- `functions/selectors/test_before_3.py`, `test_after_3.py`,
  `test_from_3.py`, `test_to_3.py` (standalone directional use,
  dissimilar-direction ranging, mixed-anchor-type ranges)

#### 6.28b
- `functions/selectors/test_before_3.py::TestAliases`,
  `test_after_3.py::TestAliases` (the full alias table — `below`/`lt`,
  `above`/`gt`, etc. — confirmed registered and canonicalizing to the
  same class)

#### 6.28c
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` (same-direction-twice rejection
  tests, built alongside 6.28's own direction-function work)

#### 6.28d
- Covered by the range-anchor tests cited under 6.22/6.28 — the
  corrected (2026-10-16) `:from()`/`:to()` inclusivity is exercised by
  those same tests, not independently against this exact literal
  example string.

#### 6.29
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` `:index(n)` tests (anchor/
  direction/0-or-last-position forms)

#### 6.30
- `test_reference_finder_3.py` (`_apply_range` negative-bound handling,
  including the `end == -1` special case)

#### 6.31
- *(no test yet, deliberately deferred — David: raise in the first
  release since there's no demand; this is an explicit, signed-off
  deferral per Phase 2's own exit criteria, not a silent gap)*

#### 6.32
- Exercised via the mixed index/date-mode rejection tests in all three
  finders (`_apply_range` vs. `_apply_manifest_date_range` mixing checks)

#### 6.33
- Doc note (section intentionally removed) — not a testable claim.

#### 6.35
- `test_results_reference_finder_3.py::TestErrorCountPredicateGate`,
  `functions/well_known_files/test_definition_3.py`/`test_on_arrival_3.py`
  (the exact `:definition(:on_arrival(:not_none()))` example, built
  2026-10-17 — predicate-argument mechanism) — **UPDATED from
  "`:error_count()` is not built" (2026-08-24); fully built now,
  including its own GATE and the generalized version every other field
  accessor's own GATE (`:named_file_name()`, `:type()`, `:status()`,
  `:named_paths_name()`, etc.) reuses.**

#### 6.36
- `functions/filters/test_true_3.py`, `test_false_3.py`, `test_none_3.py`,
  `test_not_none_3.py`, `test_empty_3.py`, `test_not_empty_3.py`,
  `functions/selectors/test_regex_3.py`, `test_having_3.py` — **UPDATED
  from "1/8 built" (2026-08-24); all 8 predicate-support functions are
  now built and tested**, including `:having()`'s own two widenings
  this week (nested field-accessor argument, list argument for "any of
  these identities").

#### 6.37
- Doc pointer/conceptual framing (Point/Narrow/Match), demonstrated by
  6.38-6.40's own examples below.

#### 6.38
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` `:index(n)` tests (the exact
  pointer-needs-its-argument shape)

#### 6.39
- `functions/selectors/test_having_3.py`,
  `test_csvpaths_reference_finder_3.py::TestHaving` (`:having("...")`
  narrowing a context setter's own scope)

#### 6.40
- `test_results_reference_finder_3.py::TestErrorCountPredicateGate`
  (the exact `:error_count(:above(2))` matching shape this item
  describes, chained after `:errors()`)

#### 6.41
- `test_results_reference_finder_3.py::test_errors_with_idchain_filters_to_matching_source`
  (the file-vs-value distinction, using the same real `:idchain(
  "add[0]")` example)

#### 6.42
- `test_reference_3.py::TestInterpolatedString3`,
  `test_reference_transformer_3.py::TestStringInterpolation`,
  `test_reference_parser_3.py::TestStringInterpolationThroughParser`
  (VALUE-role-only restriction, `{{`/`}}` escaping)

#### 6.43
- `functions/test_function_3.py` (`ROLE` self-reporting — CONTEXT_SETTER/
  POINTER/VALUE — exercised via every function's own `ROLE` class
  attribute and `build_chain()`'s pointer-counting logic)

#### 6.44
- `functions/fields/test_uuid_3.py::TestSelectByUuidArgument`,
  `test_fingerprint_3.py` (the exact bare-vs-argued dual behavior this
  item describes — **UPDATED from "no test yet, dual selector behavior
  not built beyond `:fingerprint()`" (2026-08-24); `:uuid()` now has it
  too, built this week via `SELECTOR_WHEN_ARGUED`**)

#### 6.45
- Exercised throughout all three finders' own name_one pointer-
  resolution tests.

#### 6.46
- `test_results_reference_finder_3.py::test_errors_with_idchain_filters_to_matching_source`
  (file-vs-value-one-level-deeper, the exact nesting this item
  describes)

#### 6.47
- No direct test — design-philosophy note (deliberate simplicity, no
  multi-key predicates). The constraint it describes is enforced
  structurally by the grammar's own at-most-one-argument rule
  (`test_references_3_grammar.py`).

#### 6.48
- `functions/test_reference_function_factory_3.py::TestBuildChain::test_two_pointers_in_the_same_chain_raises`
  (illegal same-level case); `test_results_reference_finder_3.py::test_errors_with_idchain_filters_to_matching_source`
  (legal nested case, `:errors(:idchain(...))`)

## 7. Grammar and Implementation

#### 7.1
- No dedicated "LALR works" test — proven by construction itself
  (`Lark(REFERENCE_GRAMMAR_3, parser="lalr")` — if LALR failed to
  compile, every test in `tests/references/` would fail at parse time).
  `parse_interactive()`-based type-ahead is *(no test yet — not built;
  explicitly OUT of this v3 MVP's scope, deferred to FlightPath's own
  later work per David's 2026-10-17 call, not a silent gap)*.

#### 7.2
- `test_reference_transformer_3.py`, `test_reference_parser_3.py::TestConstruction`

#### 7.3
- `functions/test_reference_function_factory_3.py::TestBuild` (registry
  lookup/dispatch), the `_Wraps3` custom-function test in the same file
  (`add_function(cls)`)

#### 7.4
- `test_reference_finder_3.py::TestConstruction`, `TestResolve`
  (query/resolve two-stage shape, shared ABC behavior)

#### 7.5
- `test_reference_finder_3.py::test_resolve_from_list_narrows_then_only_extracts_the_selection`,
  `test_resolve_from_a_results3_does_not_requery`;
  `test_reference_results_3.py::test_trimmed_results_can_be_handed_to_resolve_from`

#### 7.6
- `test_reference_results_3.py::TestReferenceResult3` (four-field
  construction/validation — including the `path` cannot-be-None/empty
  constraint caught live this week during the `:status()` build),
  `TestReferenceResults3` (container behavior)

#### 7.7
- `test_reference_results_3.py::test_deduplicated_collapses_exact_duplicates`,
  `test_deduplicated_uses_full_equality_not_just_path`,
  `test_deduplicated_preserves_first_occurrence_order`

#### 7.8
- Exercised throughout — every finder test constructs via a
  `ReferenceParser3`, no single isolated test needed beyond that.

#### 7.9
- Confirmed piecemeal throughout this pass and earlier sessions:
  FILES/CSVPATHS/RESULTS rows via each finder's own `query()` tests;
  Rule 1a/1b rows via the global-ledger test classes cited under
  5.6/5.7 above — including the FILES-ledger `origin_path` fallback
  case caught live this week (a "failed" entry has no
  real `file_path`, confirmed by `TestStatusGate::test_star_root_matches_the_normative_example`).

---

**Phase 3 regeneration summary (2026-10-18):** of the ~180 numbered
items, the large majority are confirmed built and tested — most of the
original 2026-08-24 "no test yet" markers were closed by the intensive
build work of the preceding two weeks (direction/ordinal functions,
time-component functions, the predicate-argument GATE mechanism and its
generalization across `:error_count()`/`:named_file_name()`/`:type()`/
`:status()`/`:named_paths_name()`, the `:uuid()` dual-selector mechanism,
`:having()`'s nested-function and list arguments, and the compendium
6.7 functional taxonomy). Genuinely still open, carried forward
honestly rather than silently dropped:
- **3.3 / 5.1** — `#name_two` (XLSX worksheet marker) still not built
  anywhere.
- **5.2** — `ReferenceExpression3` has no query()-only mode; always
  resolves both sides today. Worth confirming with David whether this
  is still wanted as a distinct capability or whether the always-
  resolve design is now accepted.
- **6.31** — mixed-direction-forcing-backwards-count — explicitly,
  deliberately deferred per David's own sign-off (not a silent gap).
- **6.8** — the exact literal UNION/SUBTRACT/INTERSECT-by-uuid worked
  examples in this item have no dedicated test verbatim, though the
  underlying cross-datatype mechanism is proven elsewhere
  (`test_intersect_files_paths_left_results_values_right_is_genuinely_cross_datatype`).
- **3.9a / 3.9b / 4.3d** — three small, likely-grammar-enforced
  constraints (`name_one` can't be empty/end in `.`, can't start/end
  with `/`, `:flatten()/*` is illegal) with no test found asserting
  them by name. Low risk (malformed references of these shapes would
  fail to parse, not silently misbehave), but worth three small,
  cheap regression tests if closing every last gap matters for the RC
  decision.
- **7.1** — `parse_interactive()` type-ahead: explicitly out of this
  v3 MVP's scope (FlightPath's own later work), not a gap against this
  MVP.

No genuine spec/code *mismatch* was found during this pass — every
case above is either "not yet built" (a real, known gap) or "built but
not tested against this exact literal example" (lower-risk, the
underlying mechanism is proven elsewhere). This regeneration is docs
only — no test or production code was touched — so the full suite was
not re-run from this change itself; the most recent full
`tests/references/` run on this same codebase (PR #399, immediately
preceding this pass) passed 1894 tests.
