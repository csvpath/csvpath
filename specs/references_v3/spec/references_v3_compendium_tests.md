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
- `test_reference_grammar_3.py`, `test_reference_parser_3.py::TestConstruction`

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
- `test_reference_grammar_3.py`, `test_reference_3.py::TestFunctionCall3`

#### 3.12
- *(no test yet — no variable-registration mechanism exists on any finder
  at all; see bucket list "`@variable`" item, extended 2026-08-24 to note
  this specifically.)*

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
