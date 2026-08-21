# References v3 — Deferred Work Bucket List

A running, flat list of everything punted to a later commit/branch/design
conversation while working on references v3 — the single place to check
"how close are we." Add to this whenever something gets deferred, whether
mid-conversation or mid-code. Remove/check off an item once it's actually
built, rather than leaving it to rot.

## Grammar / argument-type gaps (spec says it should work, code doesn't yet)

- `root_major` does not accept a `:regex(...)` function — grammar only
  defines `root_major: STAR | IDENTIFIER` (`reference_grammar_3.py`), no
  function alternative at all, even though `creating references v3.txt`
  (lines 79-80) says it should. No `:regex()` *function* exists anywhere in
  v3 today, for any position (`Regex3` is a `/pattern/` *literal* type,
  usable as some other function's argument value — a different thing).
- A name_one path segment cannot be a regex either — `_compile_path_
  pattern()` only accepts `:name("...")` as a function-valued segment, and
  `Name3.ARG_TYPES = (str,)` (no `Regex3` support).
- `@variable` (`Variable3`) is parsed but not usable anywhere as a real
  argument — no currently-registered function's `ARG_TYPES` includes it.
  The only place it's structurally accepted at all is a bare `@variable`
  inside `{...}` string interpolation, and even there it can't be
  *evaluated* yet (see interpolation-evaluation item below).

## `'*'` traversal — RESULTS/CSVPATHS remaining gap

- `:manifest()` combined with real `'*'`-traversal narrowing (`:all()`/
  `:flatten()`/a literal prefix) is still unsupported, both
  `ResultsReferenceFinder3` and `CsvpathsReferenceFinder3` — the one
  traversal restriction that survived every other generalization pass.
  `_extract_data()` can't yet reliably tell a Rule-1b global-ledger result
  apart from a genuine traversal result once both carry a real uuid;
  comparing `result.path` against the ledger's own known, fixed path
  (rather than `result.uuid is not None`) is the identified fix. See
  `references_v3_compendium.md` §6 for the full writeup. **Currently the
  active next task.**
- `:groups()` combined with `'*'` traversal (RESULTS) — no established
  per-GROUP-of-named-results-groups meaning settled yet for the any-depth
  case.
- `:having()` is not yet built for RESULTS at all (only CSVPATHS has it).
  Real, wanted follow-up, not just aspirational — "give me all the runs
  where the named-paths group included a csvpath with a given identity"
  vs. "just give me the matching instances" both want this on RESULTS
  directly. See `references_expressions.md`.

## `'*'` traversal — FILES, essentially untouched by the recent RESULTS/CSVPATHS work

- `FilesReferenceFinder3`'s own `_query_star_traversal()` still rejects
  combining `'*'` traversal with `:manifest()`/`:path()`/a field-accessor
  function outright — the same class of gap RESULTS/CSVPATHS just had
  fixed (field accessors, then `:having()`/`:flatten()`/`:all()`, then
  path narrowing/`name_three`, then pointer optionality), never applied to
  FILES. FILES' traversal already never requires a pointer (confirmed —
  no fix needed there), but everything else in that generalization
  sequence hasn't been revisited for this datatype.
- FILES' `:all()`/`:groups()` (GROUP modes) combined with `:manifest()`/
  `:path()`/a field-accessor — same single-entity-vs-grouping restriction
  RESULTS' `name_three` content accessor now has, not yet built for FILES.
- A literal prefix *before* `:flatten()` for FILES, e.g. `"2025/:flatten()
  /:name('orders.csv')"` — "any `orders.csv` below 2025, at any depth in
  between." Explicitly deferred 2026-08-12 — David wants it eventually,
  not urgent. Falls through today to a clean rejection (not a silent wrong
  answer). See `files_reference_finder_3.py` (`test_a_literal_prefix_
  before_flatten_is_not_yet_supported`).
- FILES' `:from()`/`:to()` combined with `:all()`/`:groups()` grouping in
  name_one — not yet supported.
- A literal name_three body for FILES (bypassing a pointer function
  entirely) — not yet supported.

## Functions

- `:path()` does not support RESULTS at all yet (`DATATYPES = (FILES,
  CSVPATHS)`) — can't wrap RESULTS' own `:manifest()` or any well-known
  instance file (`:errors()`, `:vars()`, etc.).
- Functions named in the spec/example-queries docs with no `Function3`
  subclass yet: `:before()`/`:after()`, `:yesterday()`, `:quarter()`,
  `:choice()`, `:names()`, `:message()`, `:count()`, `:above()`,
  `:has_errors()`, `:type()`, `:at()`.

## Bigger, standing items

- **Type-ahead.** A prototype exists (`specs/references_v3/notes/
  autocomplete_prototype.py`) demonstrating the intended mechanism (Lark
  `parse_interactive()`/`InteractiveParser.choices()` plus a datatype/slot-
  filtered function registry), but it predates the merged grammar and
  isn't wired into `REFERENCE_GRAMMAR_3`/`Function3`/`describe()` at all.
- **`{...}` interpolation evaluation.** Parsing/validation is built;
  actually resolving an `InterpolatedString3` into final text at runtime
  is not — needs variable resolution (`@name` against a real `CsvPaths`/
  scope context) and something to actually call a real `VALUE`-role
  function at evaluation time.
- **v3 is not wired into production.** `results_manager.py`/
  `file_manager.py` still dispatch through the older v2 reference system
  (`csvpath/util/references/`). Everything built so far has been
  self-contained and tested independent of this integration question.

## Process note

`references_v3_compendium.md` §6 ("Known gaps")/§7 ("Not yet built at all")
cover a lot of this same ground at a more structural, spec-vs-implementation
level. This list is the lighter-weight, more granular working companion to
that — check both, but don't feel obligated to keep every item in perfect
sync between the two; this list is allowed to be the messier, more
immediate one.
