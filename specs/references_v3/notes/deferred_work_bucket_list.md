# References v3 — Deferred Work Bucket List

A running, flat list of everything punted to a later commit/branch/design
conversation while working on references v3 — the single place to check
"how close are we." Add to this whenever something gets deferred, whether
mid-conversation or mid-code. Remove/check off an item once it's actually
built, rather than leaving it to rot — moved to `deferred_work_done_list.md`
instead, so the completed reasoning trail isn't lost, it's just off this
list (see that file's own header, and the "Process note" at the bottom of
this one).

## A function following a path separator implies a `*` wildcard (compendium 3.9c/3.9d) — confirmed unimplemented, real and foundational

Surfaced 2026-09-23 while building `:regex()` as a name_one path segment
(see the done-list entry). Compendium 3.9c: "A function starting `name_one`
or following directly after a path separator implies a `*` wildcard,"
except for three exception categories — wildcards themselves (`:all()`/
`:flatten()`/`:groups()`), functions that fully occupy a path segment
(`:name()`/`:regex()`/`:choice()`), and functions that do not operate in a
path segment at all (`:manifest()`/`:definition()`/`:on_arrival()`/
`:fingerprint()`/etc). 3.9d gives concrete equivalences: `$acme.files.
orders/:type("csv")` ≡ `$acme.files.orders/*:type("csv")`, and the same
bare-at-name_one-start case (`$acme.files.:type("csv")` ≡ `$acme.files.
*:type("csv")`).

**Confirmed unimplemented anywhere** — grepped every finder/transformer for
"implie"/anything resembling this rule: nothing. Live-parsed the concrete
consequence: `orders/:regex("202[6789]")/EMEA/:last()` (an EARLIER, since-
corrected draft of the `:regex()` worked example, David's own typo) parses
`:last()` as a literal element of `name_one.path` (a '/' before it puts it
there, not into `name_one.functions`, the trailing-pointer position every
other worked example in the doc uses) — `_compile_path_pattern()` then
raises, since `:last()` is not `:name()`/a clock function. Per 3.9c/3.9d,
this should instead be read as `orders/:regex(...)/EMEA/*:last()` — the
bare pointer, run after a path separator with nothing else, implying a
wildcard segment for it to reduce.

**RESULTS half BUILT 2026-09-24** — see `deferred_work_done_list.md` for
the full writeup (design reasoning, the exemption list's own subtleties,
and a genuine clarification this surfaced: `*`/an implied `*` represents
the entity's own TERMINAL slot, not a level above it — confirmed against
David directly after an initial, wrong analysis).

**FILES investigated 2026-09-24, deliberately NOT built — implied-`*` turned
out not to be the relevant fix.** First attempt wired `_apply_implied_star()`
into `FilesReferenceFinder3.query()` the same way as RESULTS and broke 29
tests — FILES has no early-return "bare X" checks for the literal-root case
the way RESULTS lacks entirely; FILES has SEVERAL (`:manifest()`/
`:definition()`/`:readme()`/`_bare_definition_field_call`/
`_bare_manifest_field_call`), all running BEFORE the point RESULTS-style
insertion was placed, so the normalization pre-empted every one of them.
Moving the call later (right before `if name_one.functions: raise`) would
have fixed that regression, but investigating further (David, 2026-09-24)
found something more fundamental: FILES' own `name_one.functions` is
*categorically rejected* today (`"does not yet support functions attached
directly to name_one"`) — unlike RESULTS, where `.functions` is a pointer's
NATURAL home. `_apply_implied_star()` moves the implied function into
`name_one.functions`, so for FILES this just relocates the error, it does
not fix anything.

David worked out the real shape of the problem with a table crossing
explicit-vs-implicit access against local-vs-global manifest scope (`:type()`
used as the example field, standing in for the not-yet-built predicate/
matching form — see the predicate-argument entry above). Empirically tested
each row live (substituting `:uuid()` for `:type()` to isolate the
structural question from `:type()`'s own missing `ARG_TYPES` support):

| reference shape | source | status |
|---|---|---|
| `$acme.files.:manifest():uuid()` | explicit, local | **already works** |
| `$acme.files.:flatten().:uuid()` | implicit, local | **already works** |
| `$acme.files.:flatten().:manifest():uuid()` | explicit, local (via name_three chain) | **already works** |
| `$*.files.:manifest():uuid()` | explicit, global | already built (confirmed via an earlier session PR; a scratch test of this specific row used a wrongly-shaped ad hoc fixture, not a real gap) |
| `$*.files.:flatten().:uuid()` | implicit, global | **fails** — see below |
| `$acme.files.:uuid()` | bare, name_one (3.9d's own shape) | fails: "not a legal name_one path segment" |
| `$acme.files.*:uuid()` | explicit `*`, name_one (3.9d's claimed equivalent) | fails: "functions attached directly to name_one" |

Two real findings from this table:
1. **A genuine, separate, narrower gap — BUILT 2026-09-25**, see
   `deferred_work_done_list.md`. `$*.files.:flatten().:uuid()` (global,
   implicit, no real pointer) used to raise `"FilesReferenceFinder3 requires
   name_three to resolve to exactly one pointer function... when traversing
   every named-file with '*'"` — `_query_star_traversal()` was stricter
   about this than the literal-root path, which has no such restriction for
   a bare field accessor riding alongside `:flatten()`'s own pooling.
2. **Implied-`*` itself is not the blocker for the other two failing rows.**
   Both `$acme.files.:uuid()` (bare) and `$acme.files.*:uuid()` (explicit)
   fail today — 3.9d's own claimed-equivalent EXPLICIT form is *already*
   broken, for the same reason the bare/implied form would be even after
   normalization: FILES has no general "a wildcard/marker in name_one with a
   chained field function" mechanism, only the two special-cased bare-chain
   shapes (`:manifest()`-rooted, `:definition()`-rooted). Building
   implied-`*` for FILES would only relabel `:uuid()`'s error message from
   one rejection to a slightly different one — it would not make either row
   work.

**Conclusion, and what would actually need to be built** (not attempted
here): the real prerequisite is generalizing FILES' `name_one.functions`
handling to accept a wildcard/marker (`*`/`:all()`/`:flatten()`/`:groups()`)
combined with a chained field-accessor function — separate, somewhat larger
work than implied-`*`, and not obviously worth doing in isolation before the
predicate-argument mechanism exists anyway, since a bare (non-matching)
field read via this shape is not a case any worked example has asked for.
Once (if) that lands, implied-`*` would then trivially normalize the bare
form into it, with no further work. `ReferenceFinder3._apply_implied_star()`
itself stays built and shared (RESULTS already uses it) — nothing about it
needs to change when FILES support is eventually picked back up.

## `:file_name()` — Named-File Arrivals Manifest field with no accessor

Surfaced 2026-09-22, sweeping `csvpath/references/functions/fields/` (84
files) against `references_v3_required_manifest_functions.md`'s 9 manifest
tables. Table 2 (Named-File Arrivals Manifest, global) lists a `file_name`
field ("The named of the original physical file that was registered. This
is the same name as the file home directory") mapped to `:file_name()` —
not registered anywhere. Unlike `:named_paths_home()` (built 2026-09-22,
see `deferred_work_done_list.md`), there is no obvious sibling function to
model this on directly: `:file_home()` returns the directory *path*, not
the bare name, and it is not yet confirmed whether `file_name` is meant to
be a trivial basename-of-`file_home` convenience or genuinely needs its own
manifest/ledger read. Not built — needs a decision on which, and whether it
is worth a dedicated function at all versus documenting that
`Nos(...).basename` on `:file_home()`'s own result already answers the same
question without a new registered name. No worked example anywhere in the
docs uses `:file_name()`, so this is a genuine open design question, not
something to guess at.

## Time component functions acting as context setters — not built at all; ROLE is currently static per function, never usage-dependent

Surfaced 2026-09-21, first pass through `csvpath/references/functions/values/`
during the test-first alignment work. This is an architectural gap, not a
rename/fix — flagging it here rather than attempting the design unsupervised.

The compendium's §6.27 series (heavily revised this same review arc) settles
a three-way split for `:yesterday()`/`:today()`/`:day()`/`:year()`/etc.:
used bare/chain-level, the function acts as a **context setter** that
dominates the rest of the chain (`$acme.files.:yesterday():last()` finds the
last registration *within* yesterday's window, per §6.27f); nested as another
function's argument, it collapses to a **point** (first moment of that
period); interpolated into a string, it **stringifies** to its coarse-grained
value. §6.43's function-role taxonomy reflects the same three roles at the
type level: `CONTEXT_SETTER`, `POINTER`, `VALUE`.

The current implementation only has the third case. Every function in
`functions/values/` (`Year3`, `Yesterday3`, `Today3`, `Day3`, `DayName3`,
`Hour3`, `Hour243`, `Minute3`, `Month3`, `MonthName3`, `Second3`) declares
`ROLE = Function3.VALUE` unconditionally, `SOURCE = "clock"`, and no
`POSITIONS` at all — confirmed against `function_3.py`'s own docstring,
which describes `SOURCE == "clock"` functions as usable only "as a name_one
path segment... or inside `{...}` string interpolation... not resolved as a
bare, standalone reference on their own." `Function3.ROLE` itself is a
single static class attribute, not something that can currently vary by
where a function sits in a chain — there is no mechanism anywhere (grepped
the finders and `function_3.py`; nothing matches "yesterday", "dominat", or
"context setter dispatch") that would let `:yesterday()` used bare narrow a
query's date range the way §6.27f describes. `$acme.files.:yesterday():last()`
— the compendium's own flagship worked example for this behavior — is not
executable today; it would either be rejected (no `POSITIONS` entry means no
legal bare/chain-level position) or misinterpreted as a literal path segment.

**Needed before this can be built**: a real design for how a finder
recognizes "this VALUE-role function is sitting bare in a chain, not nested
as an argument" and turns that into an actual date-range filter on the
candidate pool, distinct from `CONTEXT_SETTER`-role functions like
`:from()`/`:to()`, which already narrow scope but do not compute a
clock-derived value themselves. (`:before()`/`:after()` would be the same
kind of `CONTEXT_SETTER` in principle, but per the dedicated "Direction/
ordinal functions" entry below, they are not built at all yet — this
comparison is illustrative of the intended role split, not a claim that
`:before()`/`:after()` are working code today.) Likely needs its own worked examples per
datatype (files/csvpaths/results all have different "what does the anchor
apply to" semantics per §6.27f's arrival/load/runtime split) before
anything is buildable — same shape as the other still-open design items in
this file, not a quick fix.

## Archive Run Manifest `uuid` field — written to metadata but not persisted to the manifest; needs a read/write unit test

Surfaced 2026-09-20 while adding archive-ledger examples to the normative
references doc (`$*.results.:manifest():uuid("..."):run_home()` — "get the
run dir of a run containing a csvpath instance with a certain UUID").
Table 7 (Archive Run Manifest) didn't document a `uuid` field at all, only
`run_uuid` (the parent run's UUID); the per-instance execution UUID that
the example needed only existed in Table 6 (Result Instance Manifest).

David: the UUID is already copied onto the metadata from the `Result`
object at run start for that instance — it just wasn't making it through
to the manifest file. Added the write in `RunRegistrar`, and added the
corresponding `uuid` field row to Table 7
(`references_v3_required_manifest_functions.md`) — `:uuid()`, "Uniquely
identifies this csvpath statement in the run."

**Still needed**: a unit test confirming the *correct* UUID is what
actually gets read/written here. There are several UUIDs in play at the
instance level (`run_uuid`, `named_paths_uuid`, `named_file_uuid`, and now
this instance-execution `uuid`) — easy to wire up the write correctly but
still pull the wrong one, so this needs explicit verification, not just
confirmation that *a* UUID shows up in the field.

**No-repro, 2026-09-22**: attempted to confirm and fix this on a dedicated
branch (`fix/run-manifest-uuid-template-fields`), outside the references-v3
lock. Live-traced a real `collect_paths` run (both with an explicit
`template` argument and via the `template=None` fallback that reads the
named-paths group's own stored default) and compared `result.uuid` against
the actual written Table 7 entry at each step, bypassing any reference-
resolution reconstruction (reading `paths.results_manager.named_results`
directly, and the archive `manifest.json` directly). In both runs the
written `uuid` matched `result.uuid` exactly. Could not reproduce the bug
as described — likely already fixed by unrelated main-codebase work since
2026-09-20 (the write line this entry describes adding is already present
and correct), though it is also possible the original observation depended
on a scenario (different backend, different run method) not exercised
here. No code change made; no unit test added, since there is nothing
currently broken to lock in. Re-open if a concrete repro turns up.

## Results Run Manifest `template` field — written by `RunRegistrar` and read by `ResultsMetadata`, but not actually showing up on a real run

Surfaced 2026-09-20, same session as the archive-ledger `uuid` gap above,
while adding "two ways to find the template used by a run" examples to the
normative references doc. Table 5 (Results Run Manifest) didn't document a
`template` field — `template` was only present on Table 7 (Archive Run
Manifest, recorded per-instance) and Table 3 (Named-Paths Manifest, the
group's default at load time, a different thing).

David: `RunRegistrar` appears to write it and `ResultsMetadata` captures/
loads it, but it's not actually present on an actual run's manifest — a
genuine bug, not a spec gap. Filed as a GitHub issue. Added the `template`
field row to Table 5 (`references_v3_required_manifest_functions.md`) —
`:template()` — documenting the intended end state ahead of the fix, same
approach as the `uuid` entry above.

**Still needed**: the actual bug fix (why the write isn't landing despite
the code path appearing to exist), then a unit test confirming
`$*.results.:first():template()`-style access actually returns the run's
real template once fixed — don't assume the write path just needs
"turning on"; confirm what's actually breaking between `RunRegistrar` and
the file on disk.

**No-repro, 2026-09-22**: attempted to confirm and fix this alongside the
Archive Run Manifest `uuid` entry above, on the same dedicated branch. Live-
traced a real `collect_paths` run (both explicit-template and the
`template=None` fallback path) and read the actual `manifest.json` written
to the run's own directory (Table 5) directly off disk. `template` was
present and held the correct string in both cases. Could not reproduce the
bug as described, for the same reasons noted on the `uuid` entry above — no
code change made, no unit test added. Re-open if a concrete repro turns up.
Separately, while testing this, `$food.results.:last()` (a references-v3
query, not a raw manifest read) returned zero results against the very
same live run that had a real, correctly-written manifest on disk — a
different, unexplained gap, in `csvpath/references/` scope rather than
`run_registrar.py`/`results_registrar.py`. Not investigated further here
(out of scope for this branch); worth a dedicated look before assuming
`:last()` over a freshly-created run works correctly in general.

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
- `:regex(...)` as a name_one path segment for RESULTS/FILES — **BUILT
  2026-09-23**, see `deferred_work_done_list.md`. Originally surfaced
  2026-08-30 with a worked example described as "matching a run's own
  directory name by pattern" — investigated 2026-09-22, and that framing
  turned out to be imprecise, not a correct target to build against (see
  the done-list entry for the full history: a first attempt built the
  correct `:name(/pattern/)`-style fix, then got reverted because it
  looked like it did not match the item's own English description).
  David corrected the normative doc 2026-09-23 (`orders/:regex("202[6789]")
  /EMEA:last()`, proper '/' separators) confirming the ACTUAL intent was
  always the ordinary template-segment-matching shape — a genuine spec
  coverage gap in the original wording, not a different, bigger
  capability. Built as originally attempted.
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

- `FilesReferenceFinder3`'s own `_query_star_traversal()` combining `'*'`
  traversal with a field accessor riding beside the pointer in
  `name_three` (POOL and GROUP modes alike) — **BUILT 2026-08-29**, see
  `deferred_work_done_list.md`. `:manifest()` (whole-resource) still
  stays rejected here, deliberately — GROUP mode can legitimately
  produce more than one reduced candidate, and this method sets no
  `ambiguous_content_read` flag to catch resolving several whole entries
  at once (Rule 1); adding that flag correctly is its own separate,
  still-open piece of work, not bundled into this fix.

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
- FILES' `:all()`/`:groups()` (GROUP modes) combined with a chained field
  accessor (e.g. `:all().:last():uuid()`) — **BUILT 2026-08-29**, see
  `deferred_work_done_list.md`. `:manifest()` (whole-resource) combined
  with GROUP modes stays rejected, unchanged — only the field-accessor
  half of this item was ever under-specified; RESULTS had already
  settled the field-accessor case, FILES just hadn't been updated to
  match.
- A literal prefix *before* `:flatten()` for FILES — **BUILT 2026-08-27**,
  see `deferred_work_done_list.md`.
- FILES' `:from()`/`:to()` combined with `:all()`/`:groups()` grouping in
  name_one — not yet supported.
- A literal name_three body for FILES (bypassing a pointer function
  entirely) — **BUILT 2026-09-22**, see `deferred_work_done_list.md`.

## Functions

- Functions named in the spec/example-queries docs with no `Function3`
  subclass yet: `:quarter()`, `:choice()`, `:names()`, `:message()`,
  `:count()`, `:has_errors()`, `:at()`. (Corrected 2026-08-26: `:type()`
  used to be listed here too, but it was built as part of the Table 1
  field-accessor batch — confirmed live, `Type3` is registered, `NAME =
  "type"` — this list had gone stale; removed. Corrected again
  2026-08-27: `:yesterday()` was also stale — confirmed live,
  `Yesterday3` is registered, built alongside `:today()` in the "pure
  value" date/time functions batch — removed. Corrected again
  2026-09-21: `:before()`/`:after()`/`:above()` moved out — see the
  dedicated "Direction/ordinal functions" entry below; the compendium's
  §6.22-6.31 series now gives them a fully worked design, so "no design
  note to build from" no longer applies to those three.) None of the
  remaining names here have settled semantics beyond their bare mention
  in the spec/example-queries docs — unlike every other item in this
  file, there is no worked example or design note to build from, so
  picking one to build means guessing its intended behavior, not
  implementing an already-decided design.

## Direction/ordinal functions (`:before()`/`:after()` and their word aliases) — fully specced (compendium §6.22-6.31), zero implementation

Surfaced 2026-09-21, sweeping the selector functions in
`csvpath/references/functions/selectors/` against the compendium. `:from()`/
`:to()`/`:index()`/`:first()`/`:last()` all exist and are registered;
`:before()` and `:after()` do not — confirmed via `grep -rln "before\|after"
csvpath/references/functions/` (nothing) and via
`ReferenceFunctionFactory._load()`'s import list (no `Before3`/`After3`, no
`before`/`after` key in `_FUNCTIONS`). This is not a quiet gap: `:before()`/
`:after()` appear throughout the compendium's own worked examples (6.27d,
6.27e/f, 6.28d) and in three existing test files as parsed strings
(`test_reference_transformer_3.py`, `test_reference_parser_3.py`,
`test_references_3_grammar.py`'s `:before(:yesterday()):after(:date(...)):
index(3)` case) — those tests all pass today only because they exercise the
grammar/transformer layer (pure syntax), never
`ReferenceFunctionFactory.build()`, so the missing registration is invisible
to the existing suite.

The compendium's design (§6.22-6.31, all present before this session) is
complete enough to build from, unlike the placeholder entries in the
"Functions" list above:
- `:before(int|str|datetime)` / `:after(int|str|datetime)` — direction-only
  siblings of `:from()`/`:to()`, same two index/date modes, but exclusive
  (§6.29b: "less-than"/"greater-than", not "-or-equal") where `:from()`/
  `:to()` are inclusive.
- A full alias table (§6.28b): `before`≡`below`≡`lt`; `to`≡`lte`; `after`≡
  `above`≡`gt`; `from`≡`gte`. All forms with the same meaning are declared
  equivalent — i.e. potentially 9 registered names (or 9 aliases resolving
  to 4 underlying behaviors), not just 2 new functions.
- A combination rule distinct from `:from()`/`:to()`'s own (§6.28c): two
  same-direction functions (e.g. `:before()` + `:to()`) is illegal (not
  meaningful — both are upper bounds); a `:before()`/`:to()`-family function
  may pair with an `:after()`/`:from()`-family one to form a range.
- Explicit backward-counting edge case (§6.30/6.31): `:from(5):to(3)`
  ("forced to count backwards") may raise in the first release ("we have no
  demand for that functionality") but must stay grammatically legal —
  design says don't preclude it later, doesn't say build it now.

**Not attempted here** — this is a new function family (up to 9 names) plus
a new validation rule (opposite-direction pairing) layered on top of
`From3`/`To3`'s existing `POSITIONS`/`ARG_TYPES` shape, not a rename or a
small consolidation like `Host3`. Building it needs a decision on scope
first: real distinct `Before3`/`After3` classes vs. one class family with
alias `NAME`s, whether all 9 aliases ship at once or just the two primary
names initially, and how alias resolution should interact with
`ReferenceFunctionFactory._FUNCTIONS`' single-name-keyed registry (an alias
is either a second dict key pointing at the same class, or its own subclass
— both work, but pick one convention before the first one is built, so
later ones don't drift).

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
