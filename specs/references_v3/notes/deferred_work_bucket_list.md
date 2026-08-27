# References v3 — Deferred Work Bucket List

A running, flat list of everything punted to a later commit/branch/design
conversation while working on references v3 — the single place to check
"how close are we." Add to this whenever something gets deferred, whether
mid-conversation or mid-code. Remove/check off an item once it's actually
built, rather than leaving it to rot — moved to `deferred_work_done_list.md`
instead, so the completed reasoning trail isn't lost, it's just off this
list (see that file's own header, and the "Process note" at the bottom of
this one).

## Results Run Manifest has no `named_paths_fingerprint` field

Surfaced by David, 2026-08-26, while correcting the UNION `KIND`
taxonomy (see `deferred_work_done_list.md`'s "UNION compatibility
revised again... to compare by conceptual `KIND`" entry): the Results
Run Manifest (table 5) records `named_file_fingerprint` (which named-
file content drove the run) but has no equivalent field for which
named-paths group *content* drove the run — only `named_paths_uuid`
(the group version's registration identity, not its content). David's
own words: "it's not, but should be." This is what would let a run be
compared, by `:fingerprint()`/`KIND == "fingerprint"`, against the
named-paths group whose *content* (not registration event) produced it
-- catching the case where the same `group.csvpath` text was loaded
under two different names (different uuids, identical fingerprint).
Not yet built: no `NamedPathsFingerprint3` function, no manifest field,
no registrar change to populate it.

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
  and accessor is not None` check — this one IS count-based (unlike the
  one above), structurally identical in shape to the literal-root run-level
  check that WAS converted — a strong candidate to convert the same way.
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

## `resolve_kind`'s hardcoded name-tuple dispatch — needs examination for clarity/impact before deciding

Found 2026-08-22 while checking whether the compendium's old §6 ("Known
gaps") still had anything current in it. `Reference3.resolve_kind` (`reference_3.py`)
dispatches `METADATA_FILE`/`METADATA_FIELD` classification off two hardcoded
name-string tuples, `_METADATA_FILE_FUNCTIONS`/`_METADATA_FIELD_FUNCTIONS`
(now over 60 names combined, after several rounds of new field accessors
each needing their own name added by hand) — confirmed every single name in
both tuples *is* backed by a real, registered `Function3` today. So nothing
is factually broken, but the tuples have kept growing by hand with every
new batch of field accessors — a maintenance cost, and exactly the kind of
thing a declarative check would eliminate.

But the code comment sitting directly above those two tuples says: "both
lists will be replaced by real per-function trait lookups once `Function3`
exists." `Function3` (with `ROLE`/`SOURCE`) now fully exists — that refactor
was always the intended end state, and it appears to have never happened.
`resolve_kind` still dispatches off two hardcoded name lists instead of a
declarative check on the function classes themselves (e.g. `SOURCE is not
None`, or similar). This is the same *kind* of architectural debt as the
`SELECTOR_WHEN_ARGUED` idea already on this list (dual selector/value-
accessor behavior), but it is a distinct mechanism — that entry is about
declaring dual selector/value behavior; this one is about *how function
category is recognized at all* — and isn't covered by that entry.

**David, 2026-08-22: not yet clear on the meaning/impact of this one** —
needs a real look (what would break or simplify if `resolve_kind` were
switched to a declarative check, whether the two tuples could shrink to
one shared mechanism, whether this connects to the still-unrecognized
"file/well-known-file accessor" category from the four-function-types
discussion) before deciding whether/how to act on it. Flagging for
clarity, not yet a committed-to fix. Still true as of 2026-08-26 — every
new field-accessor batch since has kept adding to the tuples by hand
rather than resolving this.

**A precedent for exactly this kind of fix already exists in the codebase**
(found while scanning the old compendium copy before it was deleted):
`ReferenceFinder3._check_position()` replaced a near-identical class of
problem — scattered, hand-written, per-finder "is this recognized" guards
that silently no-opped on anything genuinely unrecognized instead of
raising (confirmed live at the time: `$acme.csvpaths.:name("x")`, a
FILES-only function, silently did nothing instead of erroring). The fix
was a declarative `Function3.POSITIONS: dict[datatype, tuple[position,
...]]` class attribute, checked centrally by one shared `_check_position()`
call, rolled out incrementally one finder at a time. Whatever `resolve_kind`
ends up doing should probably follow the same template (a declarative
class attribute + one shared check) rather than inventing a new pattern.

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

- **`:uuid(known_uuid)` should select the entity whose uuid *is* that value**
  (probably via `@variable`), not just read the uuid off an already-selected
  one. Currently `Uuid3.ARG_TYPES = ()` — any argument at all is rejected
  outright.
- **`:fingerprint(...)` already does exactly this, but only for FILES, and
  only as a one-off special case** — `$alpha.files.:fingerprint('hash...')`
  (bare, sole content of name_one, with an arg) searches the whole named-
  file's manifest for the entry whose own fingerprint matches
  (`fingerprint_3.py:15-30`). `ROLE` stays `VALUE` (so it never wrongly
  counts as a second pointer riding beside a real one); the selector
  behavior is recognized structurally by a bespoke, hand-written
  `FilesReferenceFinder3._is_bare_fingerprint_reference()` check — the only
  place this pattern exists today. Not generalized to CSVPATHS/RESULTS, and
  not built for any other field accessor.
- **`:idchain("add[0]")` already does the same underlying thing, one level
  down** — it doesn't just extract a value, it filters `errors.json`'s
  array to entries whose own `"source"` field matches the given chain
  string. Same "match against your own key/field, not just read it" idea,
  applied to array elements instead of whole entities. (`ARG_REQUIRED =
  True` today — no bare, unargued form exists or is implied to mean
  anything yet.)
- **The general capability doesn't exist as a declarative mechanism** —
  each instance so far is its own hand-built, per-function, per-finder
  special case (`_is_bare_fingerprint_reference`, the pointer-adjacent
  `:home()`/`:all()`/`:flatten()`/`:groups()` structural checks). Proposed
  direction, discussed 2026-08-21 (David: "we don't need to subclass, but
  we do need to be able to indicate that certain functions may select
  files or retrieve values, depending on how they are used" — mirroring
  match functions' own `ValueProducer`/`MatchDecider` idea, but declaratively
  rather than via subclassing): a new `Function3` class attribute (e.g.
  `SELECTOR_WHEN_ARGUED`), defaulting `False`, that a single shared helper
  checks the same way `_is_bare_pointer_reference`/
  `_is_bare_fingerprint_reference` already do today, generically instead of
  one hand-written check per function. `ROLE` stays declared `VALUE`
  either way, for the same reason `Fingerprint3` already needs it to.

## Grammar / argument-type gaps (spec says it should work, code doesn't yet)

- `root_major` does not accept a `:regex(...)` function — grammar only
  defines `root_major: STAR | IDENTIFIER` (`reference_grammar_3.py`), no
  function alternative at all, even though `creating references v3.txt`
  (lines 79-80) says it should. No `:regex()` *function* exists anywhere in
  v3 today, for any position (`Regex3` is a `/pattern/` *literal* type,
  usable as some other function's argument value — a different thing).
- A name_one path segment cannot be a regex either — `_compile_path_
  pattern()` accepts `:name("...")` and any `SOURCE == "clock"` function
  (widened 2026-08-26, see `deferred_work_done_list.md`'s date/time-
  functions entry) as function-valued segments, but not a regex, and
  `Name3.ARG_TYPES = (str,)` (no `Regex3` support).
- `@variable` (`Variable3`) registration and `{...}` interpolation
  evaluation are both **built 2026-08-26** — see `deferred_work_done_list.md`.
  Still not built: `@variable` used as some OTHER function's *own direct
  argument* (e.g. a hypothetical `:uuid(@myvar)`, per the dual-selector/
  value-accessor entry above) — no currently-registered function's
  `ARG_TYPES` includes `Variable3` at all. This is a separate,
  independent gap from interpolation, not shared machinery — nothing
  about the registration API or `_resolve_value()` built for
  interpolation would need to change to also cover this, it is a
  per-function `ARG_TYPES` question.

## `'*'` traversal — RESULTS/CSVPATHS remaining gap

The `:manifest()`-combined-with-narrowing gap this section used to track,
and a stale-entry correction, are both done — see
`deferred_work_done_list.md`. Still open:

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
  combining `'*'` traversal with `:manifest()`/`:definition()`/a field-
  accessor function outright — the same class of gap RESULTS/CSVPATHS
  just had fixed (field accessors, then `:having()`/`:flatten()`/`:all()`,
  then path narrowing/`name_three`, then pointer optionality), never
  applied to FILES. FILES' traversal already never requires a pointer
  (confirmed — no fix needed there), but everything else in that
  generalization sequence hasn't been revisited for this datatype.
  (`:definition()` added by name 2026-08-21 — previously only `:manifest()`
  was called out here, but it has the identical gap, confirmed below.)

- **Concrete worked example motivating this (David, 2026-08-21)**: "which
  named-files have `on_arrival` set" needs `$*.files.:home():definition
  (:on_arrival(:not_none()))` — every named-file, zero-level (no-template)
  registrations only, with `definition.json`'s `on_arrival` field present.
  Live-tested each piece independently (dropping the not-yet-built
  predicate, since it can't even parse) to confirm exactly what's missing,
  rather than assuming one gap covers it — turns out this one reference
  needs **four independent fixes**, not one:
  1. Typo aside (`home()` needs its leading colon), `:home()` + `'*'`
     traversal doesn't exist — `$*.files.:home()` alone raises `"Does not
     yet support :home() as a name_one path segment."` `:home()`'s
     zero-level-selector behavior (`_is_bare_home_reference`) was only ever
     built for a literal root_major, never extended to traversal.
  2. `:definition()` + `'*'` traversal doesn't exist either — same
     rejection, confirmed independently. `:definition()` is only wired for
     the literal-root bare case (`_is_bare_pointer_reference`); nothing
     routes it through `_query_star_traversal` at all.
  3. Chaining them together is *separately* blocked even once #1/#2 are
     fixed — `$*.files.:home():definition()` raises a different, more
     specific error: `"does not yet support functions attached directly to
     name_one for '*' traversal."` A dedicated guard rejects any
     function-in-name_one during `'*'` traversal, so fixing `:home()` and
     `:definition()` individually would not automatically make the
     combination work.
  4. The predicate itself, `:on_arrival(:not_none())` — see the
     predicate-argument entry above; not built anywhere, independent of
     all three traversal issues above.

  Use this reference as the acceptance test once all four pieces are
  built: `$*.files.:home():definition(:on_arrival(:not_none()))` should
  return exactly the zero-level named-files whose `definition.json` has a
  non-`None` `on_arrival`.
- FILES' `:all()`/`:groups()` (GROUP modes) combined with `:manifest()`/
  a field-accessor — same single-entity-vs-grouping restriction RESULTS'
  `name_three` content accessor now has, not yet built for FILES.
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

- Functions named in the spec/example-queries docs with no `Function3`
  subclass yet: `:before()`/`:after()`, `:yesterday()`, `:quarter()`,
  `:choice()`, `:names()`, `:message()`, `:count()`, `:above()`,
  `:has_errors()`, `:at()`. (Corrected 2026-08-26: `:type()` used to be
  listed here too, but it was built as part of the Table 1 field-accessor
  batch — confirmed live, `Type3` is registered, `NAME = "type"` — this
  list had gone stale; removed.)

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
