# References v3 Compendium — Test Conformance Map

Maps each numbered item in `references_v3_compendium.md` (`#### N.M`
headings) to the test(s) that verify it. Built and kept current during
Phase 1 of `specs/references_v3/notes/rc_roadmap.md` (the block-by-block
compendium review), not all at once up front.

**Conventions:**
- One `#### N.M` heading per compendium item, in the same order as the
  compendium itself.
- Below each, a bullet list of `test_file.py::TestClass::test_method`
  references that verify it. Many-to-many is normal and expected -- an
  item may need several tests to cover fully (e.g. one per datatype row
  in a table), and one test may verify several items at once; list it
  under each item it actually covers, don't force a false 1:1.
- An item with no test yet is marked explicitly, `- *(no test yet)*` --
  never leave it silently blank. A visible gap here is exactly the
  "tests needed" signal Phase 1 is supposed to produce, and doubles as a
  live view into how much of the compendium is actually proven versus
  just asserted.
- Kept as a separate file from the compendium on purpose (David,
  2026-08-24) -- keeps the compendium itself concise and readable as pure
  directive requirements, while still letting every claim be traced to
  real, running proof.

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

## 3. The reference syntax model

#### 3.1
- Doc pointer only, not independently testable.

#### 3.2
- `test_references_3_grammar.py`, `test_reference_parser_3.py::TestConstruction`

#### 3.3
- *(no test yet — `#name_two` is not built anywhere yet, including for
  FILES; see bucket list "`#name_two` (XLSX worksheet marker)")*

#### 3.4
- `test_reference_3.py::TestReference3` (root_major parsing/round-trip)

#### 3.5
- *(no test yet — root_major cannot be a regex today; grammar is
  `root_major: STAR | IDENTIFIER`, no function/regex alternative. See
  bucket list "Grammar / argument-type gaps.")*

#### 3.6
- `test_files_reference_finder_3.py`, `test_results_reference_finder_3.py`
  (path-segment matching, exercised throughout both files' finder tests)

#### 3.7
- *(no test yet — no `:regex()` function exists anywhere in v3 today, for
  any position; same bucket-list item as 3.5.)*

#### 3.8
- `test_files_reference_finder_3.py::TestStarFlattensAcrossAllFiles`
  (empty-prefix / no-template case), `test_results_reference_finder_3.py`
  (equivalent no-template run cases)

#### 3.9
- `test_csvpaths_reference_finder_3.py` (version-selecting name_one,
  exercised throughout)

#### 3.10
- Doc pointer only, not independently testable.

#### 3.11
- `test_references_3_grammar.py`, `test_reference_3.py::TestFunctionCall3`

#### 3.12
- *(no test yet — no variable-registration mechanism exists on any finder
  at all; see bucket list "`@variable`" item. David, 2026-08-24: this is
  RC-blocking, not low-priority — the compendium's own wording here was
  corrected accordingly.)*

#### 3.13
- *(no test yet — same gap as 3.5, restated here.)*

#### 3.14
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` date-mode `:from()`/`:to()` tests
  (per-datatype "date of arrival/load/run" semantics)

#### 3.15
- `test_files_reference_finder_3.py` (name_three version selection),
  `test_csvpaths_reference_finder_3.py` (statement identity),
  `test_results_reference_finder_3.py` (instance result selection)

#### 3.16
- `test_results_reference_finder_3.py::TestErrorsFunction` (file retrieval
  and `:idchain()` field-match), field-accessor tests under
  `tests/references/functions/` (metadata field retrieval)

#### 3.17
- `test_normative_examples_files.py`, `test_normative_examples_csvpaths.py`,
  `test_normative_examples_results.py` (structure table's own per-datatype
  behavior, exercised end to end)

#### 3.18
- `test_results_reference_finder_3.py::TestBareFunctionOnlyNameOne` (zero
  level), star/`:all()`/`:flatten()`/`:groups()` tests in the same file
  (one/any-depth rows)

#### 3.19
- `test_files_reference_finder_3.py` / `test_results_reference_finder_3.py`
  `:home()` bare-zero-level tests

#### 3.20
- `test_reference_3.py::TestReference3::test_check_valid_rejects_bare_trailing_star`,
  `test_check_valid_rejects_star_trailing_after_a_literal_segment`,
  `test_check_valid_allows_star_followed_by_a_literal_segment`,
  `test_check_valid_allows_star_with_name_ones_own_trailing_function`,
  `test_check_valid_allows_star_with_name_three`

#### 3.21
- Same as 3.20 (illegality rule) plus 3.22's worked example (flatten-vs-
  group behavior)

#### 3.22
- `test_files_reference_finder_3.py::TestStarFlattensAcrossAllFiles`
  (the alpha/beta worked example, matching the compendium's own EXAMPLE
  SCENARIO exactly)

#### 3.23
- Same fixture as 3.22 — arrival/manifest-order assertion is built into
  that same test (beta listed first in the fixture specifically to catch
  a regression here, per the test file's own comment)

#### 3.24
- `test_results_reference_finder_3.py::TestStarTraversalPathNarrowingAndNameThree::test_star_body_on_name_three_not_supported`

#### 3.25
- Same as 3.24 (the rule this explains) — no separate test needed beyond
  3.24's own rejection test.

## 4. Query vs. Resolve

(Renumbered 2026-08-25 after David's edit added 4.3-4.8 and shifted
everything below — this section replaces the pre-edit 4.1-4.16 mapping
entirely.)

#### 4.1
- Path/uuid: exercised throughout. `identity` doing double duty for
  worksheet name (files) / instance ID (csvpaths) is *not yet built* for
  the worksheet case — see bucket list "`#name_two`" item. The "three
  fields at query()" framing is confirmed consistent with 6.6's own field
  table — no separate new `ReferenceResult3` fields implied.

#### 4.2
- *(no test yet — the "reference expression may combine two references...
  without further resolution" query()-only mode does not exist; see
  bucket list "`ReferenceExpression3` has no query()-only mode" item.)*

#### 4.3
- *(no test yet — the query()-always-succeeds/resolve()-raises-on-
  multi-match split is not built; `:path()` retirement/Rule 1 move from
  `query()` to `resolve()` is still on the bucket list. This is the
  single most consequential not-yet-built item in this whole section —
  everything else in 4.4-4.8 already works, this general rule doesn't
  yet.)*

#### 4.4
- `test_files_reference_finder_3.py::TestGlobalArrivalsLedger`,
  `test_results_reference_finder_3.py::TestGlobalArchiveLedger`,
  `test_csvpaths_reference_finder_3.py::TestGlobalLoadsLedger` (Rule 1a,
  bare `'*'`+`:manifest()`)

#### 4.5
- Same `TestGlobalArrivalsLedger`-family tests as 4.4 — `uuid=None`,
  `path`/`identity` assertions on the bare ledger result

#### 4.6
- `test_results_reference_finder_3.py` (ledger record vs. instance-file
  distinction — exercised via `TestGlobalArchiveLedger` alongside
  `TestResultInstanceManifest`-style per-instance tests; no single test
  isolates the *distinction* itself, both sides are separately covered)

#### 4.7
- `test_files_reference_finder_3.py::TestGlobalArrivalsLedgerOrdinalIndexing`,
  `test_results_reference_finder_3.py::TestGlobalArchiveLedgerOrdinalIndexing`,
  `test_csvpaths_reference_finder_3.py::TestGlobalLoadsLedgerOrdinalIndexing`
  (Rule 1b — `uuid=None` for multiple, real uuid for one ordinal-selected
  entry)

#### 4.8
- `test_files_reference_finder_3.py::test_star_with_definition_is_still_not_supported`
  (and the CSVPATHS/RESULTS equivalents in their own finder test files)

#### 4.9
- `test_reference_3.py::TestResolveKind`, per-datatype resolve tests
  throughout `test_files_reference_finder_3.py`/
  `test_csvpaths_reference_finder_3.py`/`test_results_reference_finder_3.py`

#### 4.10
- `test_results_reference_finder_3.py` (bare pointer resolve -> `None`
  cases)

#### 4.11
- Exercised throughout the three finders' own name_one-terminal query()
  tests.

#### 4.12
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` (name_one-terminal query() path
  assertions, one per datatype row)

#### 4.13
- Same three files' name_three-terminal query() tests

#### 4.14
- `test_reference_3.py::TestResolveKind` (all three `resolve_kind` values)

#### 4.15
- `test_reference_3.py::TestResolveKind::test_first_party_when_no_name_three_and_no_name_one_functions`,
  `test_first_party_for_ordinary_selector_function_with_nested_arg`

#### 4.16
- `test_reference_3.py::TestResolveKind::test_metadata_file_for_plain_well_known_file_function`

#### 4.17
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` `:manifest()`/`:definition()`
  content tests

#### 4.18
- `test_reference_3.py::TestResolveKind::test_metadata_field_when_value_locator_nested_in_terminal_function`

#### 4.19
- `test_results_reference_finder_3.py::test_errors_with_idchain_filters_to_matching_source`,
  `test_errors_with_idchain_no_match_returns_empty_list`,
  `test_errors_with_idchain_regex_filters_by_search_not_full_match` (the
  three *filter* examples — lines 1-3 of the worked set). *(No test yet
  for the two *gate* examples (lines 4-5) — `:idchain()` chained after
  `:errors()` isn't built; see bucket list "Predicate-argument field
  accessors" item.)*

#### 4.20
- Same as 4.19 — this is the explanatory note for the same worked
  example, not a separate testable claim.

#### 4.21
- `test_normative_examples_files.py`/`test_normative_examples_csvpaths.py`/
  `test_normative_examples_results.py` (resolve matrix cells, exercised
  end to end per datatype)

#### 4.22
- `test_reference_finder_3.py` (`resolve_from()` with an explicit
  `:uuid(...)` selection), `test_files_reference_finder_3.py`/
  `test_results_reference_finder_3.py` equivalent selection tests

#### 4.23
- `test_files_reference_finder_3.py::TestStarFlattensAcrossAllFiles`
  (the exact reference used in this pseudocode example). The trailing
  "resolve() will raise if more than one path" caveat has no test of its
  own here since it doesn't apply to this specific example (`:last()`
  already guarantees exactly one match) — see 4.3's own not-yet-built
  note for where that general rule actually needs covering.

## 5. Functions

#### 5.1
- `test_references_3_grammar.py`, `test_reference_3.py::TestFunctionCall3`
  (form/argument-count parsing, exercised throughout)

#### 5.2
- `test_reference_3.py::TestFunctionCall3`, `TestVariable3`, `TestRegex3`,
  `TestStar3` (one test family per argument kind)

#### 5.3
- `functions/test_reference_function_factory_3.py` (name-keyed registry
  lookup, exercised via every function's own construction test)

#### 5.4
- `functions/test_function_3.py` (`describe()` returns a dict — tests the
  *existing* structured-data method). *(No test for actual markdown
  rendering — that capability doesn't exist; see bucket list
  "`Function3.describe()` has no markdown-rendering capability" item.)*

#### 5.5
- `test_reference_3.py::TestResolveKind` (the four/three-category split is
  really `resolve_kind`'s three values plus the not-yet-declarative
  "file/well-known-file accessor" category — see bucket list
  "`resolve_kind`'s hardcoded name-tuple dispatch" item)

#### 5.6
- `test_files_reference_finder_3.py`/`test_results_reference_finder_3.py`
  (the "more than one candidate + content accessor" guards, e.g.
  `TestManifestCombinedWithNameThree`-style tests) — note this rule is
  mid-migration per 4.3's own not-yet-built query()/resolve() split; the
  *behavior* 5.6 describes is tested today via `query()`-time raises that
  are slated to move to `resolve()`-time

#### 5.7
- *(no test yet, by definition — this is the field-accessor-coverage audit
  itself; see bucket list "Field-accessor coverage against real manifest
  fields — audited 2026-08-24" item, 28/82 built)*

#### 5.8
- Doc pointer only, not independently testable.

#### 5.9
- `tests/references/functions/well_known_files/` (one test file per
  built accessor). *(`:printouts()`/`:log()` have no test — not built;
  see bucket list item.)*

#### 5.10
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` (per-instance/per-run/per-group
  manifest.json existence, exercised throughout)

#### 5.11
- `functions/well_known_files/test_definition_3.py` (optional/absent
  `definition.json` handling)

#### 5.12
- `test_files_reference_finder_3.py::TestGlobalArrivalsLedger` (bare
  `:manifest()`), `TestGlobalArrivalsLedgerOrdinalIndexing` (`:last()`
  combined) — the exact two examples given here

#### 5.13
- *(no test yet — `:on_arrival(:not_none())` predicate-argument mechanism
  is not built; see bucket list "Predicate-argument field accessors"
  item)*

#### 5.14
- Exercised implicitly wherever a finder test covers a missing/absent
  manifest or definition file — no single test isolates all three listed
  cases together.

#### 5.15
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` (manifest shape per schema,
  exercised via real fixture data throughout)

#### 5.16
- `functions/well_known_files/test_manifest_3.py`,
  `test_files_reference_finder_3.py::TestManifestCombinedWithNameThree`
  (all three worked examples, already confirmed live earlier this pass)

#### 5.17
- `:before()`/`:after()` — *(no test yet, not built)*. `:from()`/`:to()`/
  `:index()`/`:last()`/`:first()` — exercised extensively throughout all
  three finders' own range/pointer tests.

#### 5.18
- No direct test (conceptual framing) — the underlying claim (positional
  ordering reflects arrival order) is tested via `_run_dir_sort_key`
  behavior and the FILES/RESULTS worked examples (3.22/3.23's tests).

#### 5.19
- Date-mode `:from()`/`:to()` tests across all three finders (arrival/
  load/run date filtering)

#### 5.20
- `test_csvpaths_reference_finder_3.py` (statement-range `:from()`/`:to()`
  tests — index-mode only, date-mode explicitly rejected there)

#### 5.21
- No direct test — this is the conceptual Anchor/Direction/Stepping
  framework, not itself a behavioral claim.

#### 5.22
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` date-mode range tests (anchors);
  `:yesterday()` itself has *(no test yet — not built)*.

#### 5.23
- Covered by the same `:from()`/`:to()`/`:before()`/`:after()` tests as
  5.17 — `:before()`/`:after()` still *(no test yet — not built)*.

#### 5.24
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` `:index()`/range-bound tests

#### 5.25
- `test_reference_finder_3.py` (`_apply_range` negative-bound handling,
  including the `end == -1` special case this example relies on)

#### 5.26
- *(no test yet, deliberately deferred — David: raise in the first
  release since there's no demand; not yet built either way, not on the
  bucket list per his own explicit "defer the decision" call)*

#### 5.27
- Exercised via the mixed index/date-mode rejection tests in all three
  finders (`_apply_range` vs. `_apply_manifest_date_range` mixing checks)

#### 5.28
- Doc note (TBD), not a testable claim.

#### 5.29
- `functions/selectors/test_date_3.py` (`:date()` only). *(`:year()`,
  `:month()`, `:month_name()`, `:day()`, `:day_name()`, `:hour()`,
  `:hour_24()`, `:minute()`, `:second()`, `:yesterday()`, `:today()` all
  have no test — not built; see bucket list "pure value date/time
  functions" item, 1/11 built.)*

#### 5.30
- *(no test yet — the whole worked example needs the FILES `'*'`-
  traversal + predicate-argument mechanism; see bucket list "'*'
  traversal — FILES" worked-example entry, confirmed four independent
  fixes needed)*

#### 5.31
- `functions/selectors/test_having_3.py` (`:having()` only). *(`:true()`,
  `:false()`, `:none()`, `:not_none()`, `:empty()`, `:not_empty()`,
  `:regex()` all have no test — not built; see bucket list "predicate
  support functions" item, 1/8 built.)*

#### 5.32
- No direct test — conceptual framing (Point/Narrow/Match), demonstrated
  by 5.33-5.36's own examples.

#### 5.33
- `test_files_reference_finder_3.py`/`test_csvpaths_reference_finder_3.py`/
  `test_results_reference_finder_3.py` `:index(n)` tests

#### 5.34
- `functions/selectors/test_having_3.py`,
  `test_csvpaths_reference_finder_3.py` (`:having("...")` filtering)

#### 5.35
- *(no test yet — `:error_count()` is not built, and the chained-gate
  mechanism itself is not built; see bucket list "Predicate-argument
  field accessors" item's confirmed 5-example acceptance criteria)*

#### 5.36
- `test_results_reference_finder_3.py::test_errors_with_idchain_filters_to_matching_source`
  (the exact example given here — nested filter, already shipped)

#### 5.37
- `test_reference_3.py::TestInterpolatedString3`,
  `test_reference_transformer_3.py::TestStringInterpolation`,
  `test_reference_parser_3.py::TestStringInterpolationThroughParser`

#### 5.38
- *(no test yet for actual evaluation — parsing/validation only, per
  5.38's own text; see bucket list "`{...}` interpolation evaluation"
  item)*

#### 5.39
- `functions/test_function_3.py` (`ROLE` self-reporting, exercised via
  every function's own `ROLE` class attribute and `build_chain()`'s
  pointer-counting logic)

#### 5.40
- *(no test yet — `:uuid("...")`/`:fingerprint()` bare-vs-argued dual
  selector behavior beyond `:fingerprint()`'s own existing one-off case is
  not built; see bucket list "Function self-documentation — dual
  selector/value-accessor behavior" item)*

#### 5.41
- Exercised throughout all three finders' own name_one pointer-resolution
  tests.

#### 5.42
- `test_results_reference_finder_3.py::test_errors_with_idchain_filters_to_matching_source`
  (the file-vs-value distinction this describes, using the same real
  `:idchain("add[0]")` example)

#### 5.43
- No direct test — this is a design-philosophy note (deliberate
  simplicity, no multi-key predicates), not itself a behavioral claim.
  The constraint it describes (no two-arg functions, no combined
  predicates) is enforced structurally by the grammar itself
  (`test_references_3_grammar.py`, at-most-one-argument parsing).

#### 5.44
- `functions/test_reference_function_factory_3.py::TestBuildChain::test_two_pointers_in_the_same_chain_raises`
  (the illegal same-level case); `test_results_reference_finder_3.py::test_errors_with_idchain_filters_to_matching_source`
  (the legal nested case, `:errors(:idchain(...))`)

## 6. Grammar (`csvpath/references/reference_grammar_3.py`)

#### 6.1
- No dedicated "LALR works" test — proven by construction itself
  (`Lark(REFERENCE_GRAMMAR_3, parser="lalr")` in `reference_grammar_3.py`
  — if LALR failed to compile this grammar, every test in
  `tests/references/` would fail at parse time, not just a dedicated
  one). `parse_interactive()`-based type-ahead itself is *(no test yet —
  not built; see bucket list "Type-ahead" item)*.

#### 6.2
- `test_reference_transformer_3.py`, `test_reference_parser_3.py::TestConstruction`

#### 6.3
- `functions/test_reference_function_factory_3.py::TestBuild`
  (registry lookup/dispatch), the `_Wraps3` custom-function test in the
  same file (`add_function(cls)` — confirmed real, exists at
  `reference_function_factory_3.py:142`)

#### 6.4
- `test_reference_finder_3.py::TestConstruction`, `TestResolve`
  (query/resolve two-stage shape, shared ABC behavior)

#### 6.5
- `test_reference_finder_3.py::test_resolve_from_list_narrows_then_only_extracts_the_selection`,
  `test_resolve_from_a_results3_does_not_requery`;
  `test_reference_results_3.py::test_trimmed_results_can_be_handed_to_resolve_from`

#### 6.6
- `test_reference_results_3.py::TestReferenceResult3` (four-field
  construction/validation), `TestReferenceResults3` (container behavior)

#### 6.7
- `test_reference_results_3.py::test_deduplicated_collapses_exact_duplicates`,
  `test_deduplicated_uses_full_equality_not_just_path`,
  `test_deduplicated_preserves_first_occurrence_order`

#### 6.8
- Exercised throughout — every finder test constructs via a
  `ReferenceParser3`, no single isolated test needed beyond that.

#### 6.9
- Confirmed piecemeal throughout this Phase 1 pass and earlier sessions:
  FILES/CSVPATHS/RESULTS rows via each finder's own `query()` tests;
  Rule 1a/1b rows via the global-ledger test classes cited under 4.4/4.7
  above.

---

**End of Phase 1 first pass** (2026-08-25) — all six numbered sections
of the compendium have been reviewed block by block and mapped here.
Remaining work: the bucket list itself (Phase 2 — closing the gaps found
during this pass), plus re-verifying this map stays in sync as David's
own editing continues.
