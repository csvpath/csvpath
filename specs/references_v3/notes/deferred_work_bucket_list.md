# References v3 — Deferred Work Bucket List

A running, flat list of everything punted to a later commit/branch/design
conversation while working on references v3 — the single place to check
"how close are we." Add to this whenever something gets deferred, whether
mid-conversation or mid-code. Remove/check off an item once it's actually
built, rather than leaving it to rot — moved to `deferred_work_done_list.md`
instead, so the completed reasoning trail isn't lost, it's just off this
list (see that file's own header, and the "Process note" at the bottom of
this one).

## `'*'`-traversal content-accessor guards — candidates for the same query()/resolve() split, not yet re-audited

Left over from retiring `:path()`/moving Rule 1 to `resolve()` (see
`deferred_work_done_list.md`) — that pass deliberately touched only each
finder's own LITERAL-root `query()` method, per its own explicit scoping
note ("re-audit case by case once this lands, rather than assuming it
dissolves everything at once"). These are the concrete, now-identified
candidates for that re-audit, all still unconditional/immediate raises in
`query()` today, none yet converted to the
`ReferenceResults3.ambiguous_content_read` deferred-to-`resolve()` pattern:

- `ResultsReferenceFinder3._query_star_traversal()`'s own `match_all and
  accessor is not None` check (instance-level `:all()` + a well-known-file
  accessor, during `'*'` traversal) — the literal-root twin of this was
  deliberately left as an unconditional raise too (see the done-list entry
  below), not converted, so this one should be decided together with that
  one, not in isolation.
- `ResultsReferenceFinder3._star_pool_and_reduce()`'s `len(run_homes) > 1
  and accessor is not None` check — **converted 2026-08-27**, see
  `deferred_work_done_list.md`. Confirmed safe before converting: this
  branch only runs when `pointer is None`, so there is no per-partition
  reduction anywhere nearby to conflate with, unlike the GROUP-mode cases
  below.
- `ResultsReferenceFinder3._star_group_and_reduce()`'s `accessor is not
  None and pointer is not None` check (`'*'`-traversal GROUP mode + a
  content accessor) — mirrors FILES'/CSVPATHS' own GROUP-mode restrictions
  below, not obviously safe to convert (see next item).
- `FilesReferenceFinder3._query_star_traversal()`'s unconditional
  `:manifest()`/field-accessor-during-traversal rejection, and the literal-
  root `':all()'/':groups()' grouping + content accessor` rejection in
  `query()` (both files and results) — these are NOT simple count checks;
  they reject the combination outright regardless of how many entities
  would actually match. Converting them naively to a count-based deferred
  check already proved unsafe once (a CSVPATHS `:all():last():manifest()`
  test, spanning several groups each already reduced to one match via the
  pointer, is legitimate and must NOT raise) — any change here needs the
  same "was a pointer actually applied within each partition" reasoning
  the literal-root fix used, not a blind port.

## Predicate-argument field accessors (`:on_arrival(:not_none())`) — filter half built for `:idchain()`, generic mechanism still not built

David, 2026-08-21, drafting the compendium's replacement `:manifest()`/
`:definition()` section: an AI needs to answer "which named-files trigger a
run on arrival" with a direct, reliable list — not by pulling every
`definition.json` and reasoning over them itself, which only invites error
and inconsistency. Proposed shape: `$acme.files.:definition(:on_arrival
(:not_none()))` — a field-accessor function (`:on_arrival()`) taking a
predicate (`:not_none()`) as its own argument, so combined with `'*'`/
`:all()` traversal this filters which named-things survive, rather than
just transforming a value.

**Nothing like this exists today.** Two pieces are both missing:
- No filtering-by-field-value mechanism exists for FILES at all. The
  closest precedent, `:having()`, is CSVPATHS-only (`Having3.DATATYPES =
  (Reference3.CSVPATHS,)`) and does one narrow thing — checks whether a
  version's `named_paths_identities` list *contains* a given string. No
  notion of "check an arbitrary field against an arbitrary predicate."
- No predicate function (`:not_none()`, `:none()`, `:above()`, etc.) is
  registered anywhere in the codebase — confirmed via grep, nothing
  matches. `:above()` is named in the examples doc (`:count(:above(10))`)
  but is equally unbuilt.

**A second, independent precedent for the same underlying need (David,
2026-08-21)**: `:idchain("...")` as an argument to `:errors()` already
filters which errors match — not every error necessarily has an idchain,
so a `:not_none()`/`:none()` predicate would make sense there too, for the
same reason. Two separate real use cases (definition-field filtering for
FILES, error-matching for `:errors()`) both want the same underlying
predicate-argument capability — this is not a one-off, speculative ask.

**Design constraint, stated explicitly (David, 2026-08-21)**: no two-arg
functions, and no allowing multiple predicates in one reference — "some
enforced simplicity is, by my theory, beneficial, even as too much (e.g.
not having a way to do what I wrote re: on_arrival) is harmful." So the
mechanism has to be a single predicate function nested as the sole
argument to the field/error accessor it filters (`:on_arrival(:not_none())`,
`:errors(:idchain(...))`-style), never a second positional argument or a
combination of predicates ANDed/ORed together in the same call.

Needs real design work before building: how a predicate argument is
recognized/dispatched generically (one shared mechanism, not a bespoke
check per accessor function, mirroring the `SELECTOR_WHEN_ARGUED` idea
already proposed for the dual selector/value-accessor gap above), and how
it interacts with `'*'`/`:all()` traversal to actually filter survivors
rather than just transform a value.

**Part of the ambiguity is now resolved (David, 2026-08-21): "position
decides meaning."** Checked `:idchain()`'s actual current behavior against
the code first (`results_reference_finder_3.py:1102`) rather than assuming
— it is definitively a **filter** today (returns the subset of
`errors.json`'s own entries that match), never an all-or-nothing gate, and
that must not change; it is shipped, tested behavior. The two different
things "a predicate near `:errors()`" could mean turn out to already map
cleanly onto two different grammar positions, not one ambiguous shape:
- **Nested as the function's own argument** (`:errors(:idchain(...))`) —
  **filter**: narrows which entries of *that function's own content* come
  back. Already built exactly this way; do not touch.
- **A separate function chained after it**, itself carrying a nested
  predicate on an unrelated sibling field (e.g. `:errors():error_count
  (:above(5))`, hypothetical — `:error_count()` is not built either, though
  the underlying `error_count` field is real, already written to the
  manifest by `ResultsRegistrar`/`ResultRegistrar`) — **gate**: whether
  the *preceding* function's whole result is returned at all. Nothing
  dispatches this today; it is the genuinely new piece.

This rule is now written up directly in the two functions' own code
comments (`errors_3.py`, `idchain_3.py`) as the most load-bearing place for
it to live, cross-referenced to this bucket-list entry.

**Settled 2026-08-24, now in the compendium itself (§4.13/4.14)** — the
concrete, confirmed acceptance criteria for both filter and gate, using
`:idchain()` for both rather than the earlier, more speculative
`:error_count(:above(5))`-only framing:
```
$acme.results.:last().:errors()                             -- path+uuid; resolves to full content
$acme.results.:last().:errors(:idchain(:not_none()))         -- path+uuid; resolves to all errors that HAVE an idchain (filter)
$acme.results.:last().:errors(:idchain("add[0]"))            -- path+uuid; resolves to all errors matching that idchain (filter)
$acme.results.:last().:errors():idchain(:not_none())         -- path+uuid; resolves to full content, iff some idchain exists (gate)
$acme.results.:last().:errors():idchain("add[0]")            -- path+uuid; resolves to full content, iff a matching idchain exists (gate)
```
This settles the mechanism as reusing `:idchain()` in *both* positions
(nested = filter, chained = gate) rather than needing a separate, purpose-
built gate function — the predicate argument (`:not_none()`, or a literal/
`Regex3`) works the same way in either slot; only the position changes
what happens with the result.

**The FILTER half, and the six missing predicate functions themselves
(compendium 5.31) — BUILT 2026-08-26** — see `deferred_work_done_list.md`
for the full writeup (`:true()`/`:false()`/`:none()`/`:not_none()`/
`:empty()`/`:not_empty()`, a new shared `PredicateFunction3` base class,
and `Idchain3.ARG_TYPES` widened to accept one). `:regex()` as a
*function* (as opposed to `Regex3`, the literal type `:idchain()`
already accepted) is still unbuilt — separately tracked under the
grammar/argument-type-gaps entry, not double-counted here.

Still to design/build:
- **The generic "any field accessor takes a predicate argument"
  mechanism** (`:on_arrival(:not_none())`, the FILES definition-field
  example that originally motivated this whole entry) — NOT built.
  `Idchain3` accepting a predicate is a narrow, specific fix for one
  function; nothing generic exists yet for arbitrary field accessors to
  do the same. Still needs the design work described above (how a
  predicate argument is recognized/dispatched generically) before
  building.
- The actual GATE dispatch mechanism — a chained sibling function whose
  own predicate argument controls whether the *preceding* function's
  result is emitted at all — is additive to `:idchain()`'s existing filter
  behavior, not a replacement for it, and still needs building from
  scratch; nothing dispatches this today.

## `$name.files.:manifest():last()` (ordinal pointer into a single named-file's own manifest) — not built

David, 2026-08-21: raised while reviewing the compendium's `path`-per-
producer table. `$*.files.:manifest():last()` (Rule 1b) works today —
ordinal-selects one entry out of the *global* files ledger, real `uuid`
attached. By symmetry, `$acme.files.:manifest():last()` should do the same
thing one level down: ordinal-select one entry out of *acme's own*
manifest.json array, without needing a full `name_one` (`:name(...)`) +
`name_three` (pointer) reference. David: "I believe it should work that
way... regardless, the symmetry."

Confirmed by live testing it does not work today — raises:
`FilesReferenceFinder3 does not yet support functions attached directly to
name_one -- put the version-selecting function in name_three instead.`
(`files_reference_finder_3.py:169-174`). The reason: `_pointer_before_
manifest()` (the mechanism behind Rule 1b) is only invoked in the
`isinstance(root_major, Star3)` branch (`files_reference_finder_3.py:116`)
— there is no equivalent call for a literal root_major. Re-confirmed still
true 2026-08-26 (`_pointer_before_manifest` is still only called from the
`Star3` branch of `query()`, unchanged) — the related doc-example
correction (which examples were wrong, not whether this code gap exists)
was fixed separately, see `deferred_work_done_list.md`.

Open question David flagged, not yet settled: is this actually a good/
wanted alternative to a full `:name(...)` + name_three reference (which
already gets you "the matched version's own manifest entry," a different,
narrower thing), or just a symmetry nicety worth having anyway? Worth
resolving before building, not just building because Rule 1b's shape
suggests it.

## `#name_two` combined with `'*'` traversal — still not supported

Left over from building `#name_two` support for `FilesReferenceFinder3`
(see `deferred_work_done_list.md`) — deliberately scoped to the literal-
root `query()` only, same scoping discipline as the recent `:path()`/
Rule 1 and `:home()` splits. `_query_star_traversal()`'s own `#worksheet`
rejection is untouched, still unconditional. Not yet a concrete worked
example driving this — add one if/when a real use case asks for reading
a named worksheet across every named-file matched by `'*'`.

## Function self-documentation — dual selector/value-accessor behavior

The declarative `SELECTOR_WHEN_ARGUED` mechanism itself is **BUILT
2026-08-28** — see `deferred_work_done_list.md`. Still open, deliberately
NOT part of that build:

- **`:idchain("add[0]")` already does a related thing, one level down** —
  it doesn't just extract a value, it filters `errors.json`'s array to
  entries whose own `"source"` field matches the given chain string. Same
  "match against your own key/field, not just read it" idea as
  `SELECTOR_WHEN_ARGUED`, but applied to array elements inside an already-
  selected entity, not to selecting the entity itself — a different shape,
  not migrated onto the new flag. (`ARG_REQUIRED = True` today — no bare,
  unargued form exists or is implied to mean anything yet.)

- **Cross-datatype "select by known uuid" + set operations — reframed
  2026-08-28 (David), still fully open.** UUID is the connective tissue
  between *every* datatype: every place the system registers/loads
  something (a named-file version, a named-paths group version) or
  generates something (a run, a run's per-file instance) attaches a uuid
  that links it to the other datatypes. So "select an entity by a known
  uuid, and do set operations (union/intersect/exclude) across uuid-linked
  entities across datatypes" is a wide, foundational capability, not a
  one-function special case — closer in size to the predicate-argument
  mechanism above than to a single-function fix. Two separate pieces, both
  undesigned:
  1. **What "select by uuid" means per datatype** — a different lookup
     shape for a named-file entry vs. a named-paths group vs. a run vs. a
     run's file vs. a result.
  2. **What "set operations" over uuid-linked entities means** — e.g. "the
     files that fed this run," "the runs that consumed this file"; a
     genuinely new query capability, not just a selector.
  Needs worked examples per datatype before anything is buildable —
  currently `Uuid3.ARG_TYPES = ()`, any argument at all is rejected
  outright, so nothing here parses yet.

## Grammar / argument-type gaps (spec says it should work, code doesn't yet)

- `root_major` accepting a `:regex(...)` function — **BUILT 2026-08-27**,
  see `deferred_work_done_list.md`.
- `@variable` (`Variable3`) registration and `{...}` interpolation
  evaluation are both **built 2026-08-26** — see `deferred_work_done_list.md`.
  `@variable` used as some OTHER function's *own direct argument* (e.g.
  `:having(@id)`, `:regex(@aregex)` once that function exists) — **BUILT
  2026-08-27**, see `deferred_work_done_list.md`.

## `'*'` traversal — RESULTS/CSVPATHS remaining gap

The `:manifest()`-combined-with-narrowing gap this section used to track,
and a stale-entry correction, are both done — see
`deferred_work_done_list.md`. Still open:

- `:groups()` combined with `'*'` traversal (RESULTS) — no established
  per-GROUP-of-named-results-groups meaning settled yet for the any-depth
  case.
- `:having()` for RESULTS — **BUILT 2026-08-27**, see
  `deferred_work_done_list.md`.
- **`:manifest()` combined with a chained field accessor in name_one
  (e.g. `:manifest():named_file_uuid()`), silently returning the whole
  manifest entry instead of narrowing to the field — BUILT 2026-08-28**,
  see `deferred_work_done_list.md`. Turned out to be a general
  `_extract_data()` bug, not `'*'`-traversal-specific — literal root had
  the identical gap, just never exercised by a test.

## `'*'` traversal — FILES, essentially untouched by the recent RESULTS/CSVPATHS work

- `FilesReferenceFinder3`'s own `_query_star_traversal()` still rejects
  combining `'*'` traversal with `:manifest()`/a field-accessor function
  outright (`:definition()` is now the one exception, see below) — the
  same class of gap RESULTS/CSVPATHS just had fixed (field accessors,
  then `:having()`/`:flatten()`/`:all()`, then path narrowing/`name_three`,
  then pointer optionality), never applied to FILES otherwise. FILES'
  traversal already never requires a pointer (confirmed — no fix needed
  there), but everything else in that generalization sequence hasn't been
  revisited for this datatype.

- **Concrete worked example that drove this (David, 2026-08-21)**: "which
  named-files have `on_arrival` set" needs `$*.files.:home():definition
  (:on_arrival(:not_none()))` — every named-file, zero-level (no-template)
  registrations only, with `definition.json`'s `on_arrival` field present.
  Turned out to need four independent fixes, not one:
  1. **`:home()` + `'*'` traversal — BUILT 2026-08-27**, see
     `deferred_work_done_list.md`.
  2. **`:definition()` + `'*'` traversal — BUILT 2026-08-27**, see
     `deferred_work_done_list.md`.
  3. **Chaining `:home():definition()` together — BUILT 2026-08-27**, see
     `deferred_work_done_list.md`.
  4. **The predicate itself, `:on_arrival(:not_none())` — still NOT
     built.** See the predicate-argument entry above (the "any field
     accessor takes a predicate argument" mechanism it needs is still
     unbuilt). The full acceptance test
     (`$*.files.:home():definition(:on_arrival(:not_none()))`) still
     cannot parse until this lands — #1/#2/#3 were tested with the
     predicate dropped, per the done-list entry's own worked examples.
- **Bare `:manifest()` combined with one chained field accessor (e.g.
  `:manifest():uuid()`, `:manifest():time()`), literal-root and `'*'`
  alike — BUILT 2026-08-28**, see `deferred_work_done_list.md`. Driven by
  David's own worked examples ("get uuids from all registrations," "get
  all acme registration uuids"). `:all()`/`:flatten()`/`:groups()`
  combined with a chained field accessor is a related but distinct
  question (partitioning semantics differ per marker), still open, just
  below.
- FILES' `:all()`/`:groups()` (GROUP modes) combined with `:manifest()`/
  a field-accessor — same single-entity-vs-grouping restriction RESULTS'
  `name_three` content accessor now has, not yet built for FILES.
- A literal prefix *before* `:flatten()` for FILES — **BUILT 2026-08-27**,
  see `deferred_work_done_list.md`.
- FILES' `:from()`/`:to()` combined with `:all()`/`:groups()` grouping in
  name_one — not yet supported.
- A literal name_three body for FILES (bypassing a pointer function
  entirely) — not yet supported.

## Functions

- Functions named in the spec/example-queries docs with no `Function3`
  subclass yet: `:before()`/`:after()`, `:quarter()`, `:choice()`,
  `:names()`, `:message()`, `:count()`, `:above()`, `:has_errors()`,
  `:at()`. (Corrected 2026-08-26: `:type()` used to be listed here too,
  but it was built as part of the Table 1 field-accessor batch —
  confirmed live, `Type3` is registered, `NAME = "type"` — this list had
  gone stale; removed. Corrected again 2026-08-27: `:yesterday()` was
  also stale — confirmed live, `Yesterday3` is registered, built
  alongside `:today()` in the "pure value" date/time functions batch —
  removed.) None of the remaining names here have settled semantics
  beyond their bare mention in the spec/example-queries docs — unlike
  every other item in this file, there is no worked example or design
  note to build from, so picking one to build means guessing its
  intended behavior, not implementing an already-decided design.

## Bigger, standing items

- **Type-ahead.** A prototype exists (`specs/references_v3/notes/
  autocomplete_prototype.py`) demonstrating the intended mechanism (Lark
  `parse_interactive()`/`InteractiveParser.choices()` plus a datatype/slot-
  filtered function registry), but it predates the merged grammar and
  isn't wired into `REFERENCE_GRAMMAR_3`/`Function3`/`describe()` at all.
- **`{...}` interpolation evaluation — BUILT 2026-08-26**, both halves
  (function-call and `@variable`) — see `deferred_work_done_list.md`.
  `_resolve_value()`'s function-call handling is still narrow (only
  `SOURCE == "clock"` functions), worth widening once other `VALUE`-role
  functions exist that make sense inside `{...}` — not urgent, no such
  function exists yet.
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

As of 2026-08-26, completed entries live in a paired file,
`deferred_work_done_list.md`, rather than being deleted outright — the
reasoning behind *why* something was built a particular way is often
exactly what the next person touching that code needs, so it's kept in
full there rather than trimmed to a one-line changelog. When an item on
*this* list gets built, move it (with its full history) to that file
instead of just deleting it.
