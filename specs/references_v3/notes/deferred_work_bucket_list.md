# References v3 — Deferred Work Bucket List

A running, flat list of everything punted to a later commit/branch/design
conversation while working on references v3 — the single place to check
"how close are we." Add to this whenever something gets deferred, whether
mid-conversation or mid-code. Remove/check off an item once it's actually
built, rather than leaving it to rot — moved to `deferred_work_done_list.md`
instead, so the completed reasoning trail isn't lost, it's just off this
list (see that file's own header, and the "Process note" at the bottom of
this one).

## A function following a path separator implies a `*` wildcard (compendium 3.9c/3.9d) — RESULTS BUILT, FILES' direction-function error-message gap BUILT 2026-10-16, broader FILES support still deferred

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

**Conclusion, 2026-09-24** (that pass's own scope — making NEW things work,
e.g. a field accessor riding a wildcard — was not attempted): the real
prerequisite for THAT is generalizing FILES' `name_one.functions` handling
to accept a wildcard/marker (`*`/`:all()`/`:flatten()`/`:groups()`) combined
with a chained field-accessor function — separate, somewhat larger work
than implied-`*` itself, and not obviously worth doing in isolation before
the predicate-argument mechanism exists anyway, since a bare (non-matching)
field read via this shape is not a case any worked example has asked for.
That piece is still deferred, unchanged by the fix below.

**A second, narrower instance of the same gap, found and BUILT 2026-10-16
— the direction/ordinal functions' error message was wrong, not just
imprecise.** David asked whether `$a.files.:after(:index(3))` (bare) and
`$a.files.*:after(:index(3))` (explicit `*`) should be "the same" per
3.9c/3.9d. Checked `:after()` against the three exemption categories
textually: not a wildcard itself, does not fully occupy a path segment
the way `:name()`/`:regex()` do, and does not fit category 3 either
(`:manifest()`/`:definition()`/`:on_arrival()`/`:fingerprint()` are fixed
whole-entity resources; `:after()` is an ordinal/list-reducing function,
a different character). **By the letter of the spec, `:after()`/
`:before()`/`:from()`/`:to()` default into the implied-`*` rule** — the
two forms should parse to the identical normalized shape.

But implied-`*` is purely a READING rule, not a legality one — those four
functions are separately declared (`Before3`/`After3`/`From3`/`To3`'s own
`POSITIONS`) legal ONLY at `name_three` for FILES, a pre-existing,
deliberate architectural fact (`From3`'s own comment: "FILES' version
selector never lives in `name_one`"), unrelated to 3.9c/d. So even with
implied-`*` wired, the normalized shape is still illegal for FILES — just
illegal for the right reason now, instead of the wrong one. Confirmed
live both forms used to fail with two DIFFERENT and both subtly wrong
messages (the bare form via `_compile_path_pattern()` complaining about
an unrecognized PATH-SEGMENT type, which was never the real reason; the
explicit form via the pre-existing, correct "functions attached directly
to name_one" rejection).

**Fix** (branch `fix/files-implied-star-name-one-functions`): one call to
the already-shared, unchanged `ReferenceFinder3._apply_implied_star()`,
inserted at exactly one new point in `FilesReferenceFinder3.query()` —
the FINAL `else` branch (right before `pattern = self._compile_path_
pattern(name_one.path)`), reached only once every dedicated bare-shape/
field-chain check above it has already failed to match. Confirmed safe
(not a repeat of the 2026-09-24 29-test regression, which came from
inserting too EARLY, before those dedicated checks got their turn):
every branch above this point already requires `name_one.functions` to
be empty to even be considered, and the pre-existing blanket raise
higher up already intercepts anything reaching this point with
`name_one.functions` already non-empty from the grammar directly — so by
construction `name_one.functions` is guaranteed empty on entry to this
`else`, and the only way `_apply_implied_star()` can populate it here is
its own documented, already-exempted-correctly mutation. Does NOT make
`:after()`/etc. legal at `name_one` (it should not be, per FILES' own
architecture) — only makes both forms fail with the identical, accurate
message. Tests: new `TestImpliedStarForNameOneFunctions` (bare vs.
explicit-`*` raise the identical message; the "following a path
separator" clause, not just "starting name_one"; the one currently-legal
`name_three` form still works; `:name()`/clock functions remain
correctly exempt and unaffected). Full `tests/references/` suite: 1697
passed (up from 1693). Full local-backend suite: 4158 passed, 11 failed
(the known SFTP/S3 credential baseline, unrelated).

The 2026-09-24 conclusion's own larger prerequisite (generalizing
`name_one.functions` to accept a wildcard/marker combined with a chained
field accessor) remains deferred and unaffected by this fix —
`ReferenceFinder3._apply_implied_star()` needed no change at all; this
was purely about FILES' own call-site placement.

## Time component functions acting as context setters — BUILT 2026-10-17

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

### BUILT 2026-10-17 — full writeup

David: "please do the full list. I think we can extrapolate to get to Gap 2.
Please go that way." Two genuinely separate gaps, both now built, for all
ten relevant functions (`:year()`/`:month()`/`:day()`/`:hour()`/`:hour_24()`/
`:minute()`/`:second()`/`:yesterday()`/`:today()`/`:date()`) across all
three datatypes.

**Three functions deliberately excluded** from the whole mechanism, stay
plain `SOURCE == "clock"` `VALUE` functions, unchanged:
- `:now()` — §6.27g gives it only the interpolation/stringification role,
  never the three-role treatment `:yesterday()` gets; it names an instant,
  not a period.
- `:month_name()`/`:day_name()` — a bare name ("Monday", "August") has no
  year attached, so there is no single absolute date to anchor to.

**The reconciling model, confirmed with David directly** — §6.27b's literal
"first moment" text does not, by itself, reproduce either §6.27f's own
worked example or the already-shipped day-granular `:before()`/`:after()`
"excludes the whole day it names" behavior. Checked against real cases
(`:before(X)` using just X's first moment correctly excludes X's whole
period; `:after(X)` does NOT — a candidate at noon on the day X names is
"after" X's first moment but must still be excluded; `:to(X)` needs X's
*end*, not its start, for the same reason). The rule that reproduces both:
every time-bound exposes a full `[start, end]` window, and each directional
function picks whichever side suits its own direction:
```
:from(X)   keeps candidates >= X.start
:to(X)     keeps candidates <= X.end
:before(X) keeps candidates <  X.start
:after(X)  keeps candidates >  X.end
```
Bare/standalone use (Gap 1) is just the same pair used as an implicit,
always-inclusive `:from(X):to(X)`.

**A second correction, also confirmed with David**: the first draft of this
design assumed day-only truncation (`:hour()`/`:minute()`/`:second()`
collapsing to mean the same as `:today()`, since every existing date
comparison only ever compared a 10-character "YYYY-MM-DD" prefix). David
pushed back — "what is the basis for taking a finer-grained pointer and
treating it like a coarser-grained pointer?" Checked the actual data rather
than the comparison code alone: FILES/CSVPATHS manifest `"time"` fields are
full `datetime.isoformat()` strings (`metadata.py`'s own `time_string`
property), and RESULTS run directories are named `%Y-%m-%d_%H-%M-%S`
(`run_home_maker.py`) — both already carry real hour/minute/second
precision. The day-only truncation was never a property of the data, only
of the bounds that happened to exist so far (all day-granular). Fixed by
rewriting the comparison helpers to parse real `datetime` objects instead
of slicing strings, so `:hour()`/`:minute()`/`:second()` now narrow for
real.

**New shared base class**: `TimeWindowFunction3` (`csvpath/references/
functions/values/time_window_function_3.py`) — each of the ten subclasses
implements `start_datetime()`/`end_datetime()` (naive, UTC wall-clock —
tzinfo stripped so these compare cleanly against RESULTS' own tzinfo-less
run-directory datetimes). `Date3` moved here too (from a bare `Function3`)
and its own `DATATYPES` widened from `(RESULTS,)` to all three — a real,
previously-harmless gap, since FILES/CSVPATHS already accepted a
Date3-wrapped bound via `From3`/`To3`/`Before3`/`After3`'s own `ARG_TYPES`
and already ran it through the shared `_apply_manifest_date_range()`.

**Gap 2 (nested anchor, e.g. `:from(:year())`)**: `From3`/`To3`/`Before3`/
`After3.ARG_TYPES` widened from `Date3` specifically to `TimeWindowFunction3`
generically. `ReferenceFinder3._range_bound()` now returns a
`TimeWindowFunction3` instance as-is (not unwrapped) when the arg is one;
new `_bound_window(call)` resolves ANY bound (plain string or
`TimeWindowFunction3`) into a `(start, end)` pair; `_apply_manifest_date_
range()` (shared, FILES/CSVPATHS) and `ResultsReferenceFinder3._apply_date_
range()` were both rewritten around this pair and the four-way rule above,
replacing the old fixed `[:10]` string-slice comparison with real `datetime`
parsing (`_parse_manifest_time()`/`_run_dir_datetime()`, the latter renamed
from `_run_dir_date()`). Each finder's own `from_is_date`/`to_is_date`
mode-detection widened to recognize `TimeWindowFunction3` alongside `str`;
`_validate_date_format()` calls narrowed to only fire for an actual raw
string (a `TimeWindowFunction3` bound has nothing to validate that way —
`Date3` already validates its own format at construction).
`CsvpathsReferenceFinder3`'s own name_three rejection ("statements have no
arrival date of their own") widened from `Date3`-only to the same generic
check, for the same reason.

**Gap 1 (bare context setter, e.g. `:yesterday():last()`)**: detected as a
`TimeWindowFunction3` instance riding as its OWN entry in a finder's built
chain (never nested as a `:from()`/`:to()` call's own `.arg` — that is Gap 2,
structurally distinct and never conflated). New `_apply_bare_time_window()`
(RESULTS, run directories) and `_apply_bare_time_window_to_manifest()`
(shared, manifest-entry dicts) apply the bound's own `[start, end]` window,
always inclusive both ends (no separate directional function to pick
otherwise). Wired into each finder's own name_one/name_three dispatch,
right where the existing `:from()`/`:to()` range application already lived —
mutually exclusive with it (`elif`), and rejected outright if both a bare
time-component function and an explicit directional bound are present
together, or if more than one bare time-component function rides in the
same chain. **A real regression caught by the test suite before shipping**:
the ten functions' own `ROLE` was first changed `VALUE` → `CONTEXT_SETTER`
to match §6.43's own taxonomy — this broke the compendium-explicit `{...}`
interpolation usage (`:name("partner-{:year()}-orders")`, §6.42's own
worked example), since `reference_3.py`'s interpolation check hard-requires
`ROLE == VALUE`. Reverted: `ROLE` stays `VALUE` on all ten (this is, after
all, the pre-existing "ROLE is static per function, never usage-dependent"
gap this whole section used to describe) — the new bare-context-setter/
anchor capability is detected structurally instead, via `isinstance(f,
TimeWindowFunction3)`, never via `ROLE`. Also needed: `POSITIONS` added to
all ten (none had any before — a function with no `POSITIONS` entry was
only ever legal as a name_one path segment or `{...}` interpolation span,
neither of which goes through `_check_position()` at all; without this a
bare `:year()` in the chain was rejected outright). Same positions `From3`/
`To3`/`Before3`/`After3` already occupy.

**Tests**: new unit tests for each function's own `start_datetime()`/
`end_datetime()` (deterministic via `DateUtility.OFFSET_DAYS`, computed
relative to the real moment the test runs, never a hardcoded "now");
`TestTimeWindowFunctionAnchors` (RESULTS, both gaps, including the
compendium's own 6.27f flagship example verbatim —
`:from(:yesterday()):before(:today())` resolving to exactly "yesterday, the
whole day") plus one confirming test apiece for FILES/CSVPATHS (not just
assumed from the shared mechanism) — FILES' own confirming test uses the
compendium's own literal flagship example, `$acme.files.:yesterday()`.
`tests/references/`: 1789 passed (up from 1721 before this item started).
Full local-backend suite: 4250 passed, 11 failed (known SFTP/S3 credential
baseline, unrelated).

## Archive Run Manifest `uuid` field — RESOLVED, 2026-09-22 (no-repro, false alarm)

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

There are several UUIDs in play at the instance level (`run_uuid`,
`named_paths_uuid`, `named_file_uuid`, and this instance-execution
`uuid`) — easy to wire up the write correctly but still pull the wrong
one, so verification (below) checked which one actually lands here, not
just that *a* UUID shows up in the field.

**No-repro, 2026-09-22 — resolved, nothing left to do**: attempted to confirm and fix this on a dedicated
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

## Results Run Manifest `template` field — RESOLVED, 2026-09-22/28 (no-repro, false alarm)

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

**No-repro, 2026-09-22 — resolved, nothing left to do**: attempted to confirm and fix this alongside the
Archive Run Manifest `uuid` entry above, on the same dedicated branch. Live-
traced a real `collect_paths` run (both explicit-template and the
`template=None` fallback path) and read the actual `manifest.json` written
to the run's own directory (Table 5) directly off disk. `template` was
present and held the correct string in both cases. Could not reproduce the
bug as described, for the same reasons noted on the `uuid` entry above — no
code change made, no unit test added. Re-open if a concrete repro turns up.
**Resolved, 2026-09-28 — false alarm, not a bug.** Separately, while
testing the above, `$food.results.:last()` returned zero results against
the very same live run that had a real, correctly-written manifest on
disk, flagged at the time as an unexplained gap worth a dedicated look.
Traced it fully this time: the run used a 3-level template
(`test_resources/:day/:month/:run_dir`), and a bare `:last()` for RESULTS
is *supposed* to match zero-level (flat) runs only — the deliberate
degenerate-grouping semantics settled and built earlier this same session
(4.2b). Confirmed live that both `:flatten():last()` and the exact literal
3-segment prefix `:last()` correctly find the run. No code change needed
— the original flag just hadn't accounted for the run's own depth.

## `'*'`-traversal content-accessor guards — RE-AUDITED, converted or confirmed settled — BUILT 2026-09-28, partition-aware fix completed 2026-10-16

Left over from retiring `:path()`/moving Rule 1 to `resolve()` (see
`deferred_work_done_list.md`) — that pass deliberately touched only each
finder's own LITERAL-root `query()` method, per its own explicit scoping
note ("re-audit case by case once this lands, rather than assuming it
dissolves everything at once"). All four identified candidates now
resolved — see `deferred_work_done_list.md` for the full writeup,
including two genuine, previously-undetected bugs caught while doing this
(not just missing conversions):

- `ResultsReferenceFinder3._query_star_traversal()`'s own `match_all and
  accessor is not None` check — CONFIRMED SETTLED, not converted, and not
  actually a candidate: this is a structural rejection (instance-level
  `:all()` pools MULTIPLE statement instances, each with its own separate
  file — there is no pointer concept at this level to reduce it), not a
  count-dependent one. Its literal-root twin is the identical, deliberate,
  permanent rejection.
- `ResultsReferenceFinder3._star_pool_and_reduce()`'s equivalent check —
  already converted 2026-08-27, see `deferred_work_done_list.md`.
- `ResultsReferenceFinder3._star_group_and_reduce()`'s `accessor is not
  None and pointer is not None` check — **converted**. Verified each
  partition's own `_apply_pointer()` guarantees at most one selected run,
  and `_results_for_run()`'s own internal guards guarantee at most one
  `ReferenceResult3` per run whenever an accessor is present — the same
  shape already proven safe by the `:path()`-retirement fix.
- `FilesReferenceFinder3._query_star_traversal()`'s unconditional
  `:manifest()` rejection — **converted**, plus the literal-root
  `':all()'/':groups()' grouping + :manifest()` rejection in `query()` —
  **narrowed**. Same verification as above (GROUP mode reduces each
  distinct file_home to at most one candidate via the pointer).
- **Two real bugs caught in the process, not just missing conversions**:
  both the literal-root and `'*'`-traversal FILES checks were also
  incorrectly rejecting `:manifest()` combined with a CHAINED FIELD
  ACCESSOR (e.g. `:manifest():uuid()`), even though field accessors are
  exempt from Rule 1 entirely (Rule 3) and resolve_kind's own priority
  means `:manifest()` is never actually read as a whole resource in that
  shape. Confirmed live before fixing — not assumed.

  **Ready for a quick decision, then a well-specified build — found
  2026-08-29/30 while checking whether this was safe to build solo
  overnight, deliberately NOT built without a check-in first.** FILES'
  own GROUP-mode + field-accessor fix (2026-08-29, this session) narrowed
  `query()`'s `if partitioned and (has_range or (pointers and has_
  manifest)): raise` to keep `has_manifest` (whole-resource) rejected,
  precisely BECAUSE the existing `ambiguous_content_read=has_manifest and
  len(selected_candidates) > 1` flag just below it (in the shared return)
  is a NAIVE count check — it does not know whether `partitioned` is
  `True`, so it cannot currently tell "several groups, each already
  reduced to exactly one via its own pointer" (legitimate, per this very
  bucket-list item's own CSVPATHS precedent) apart from "several raw,
  unreduced candidates sharing one accessor" (a genuine Rule 1
  violation). Confirmed field accessors are unaffected by this — they
  never set `has_manifest`, so `ambiguous_content_read` is always
  `False` for them regardless of count, which is why narrowing the
  rejection to field-accessors-only was safe to ship without touching
  this flag at all (three PRs, 2026-08-28/29, none of which needed to
  touch `ambiguous_content_read`).

  To also let `:manifest()` (and any other whole-resource content
  accessor) through here, the flag itself needs to become partition-
  aware — something like `ambiguous_content_read = has_manifest and
  len(selected_candidates) > 1 and not partitioned` (or, more precisely,
  "and no per-partition pointer reduction actually happened") — mirroring
  the exact reasoning CSVPATHS' own already-shipped fix used for the
  identical shape. The SAME naive-count-check gap almost certainly also
  affects: `ResultsReferenceFinder3._star_group_and_reduce()`'s own
  `accessor is not None and pointer is not None` check (still an
  unconditional raise, not a deferred count check at all yet); and
  possibly RESULTS' own literal-root `match_all and accessor is not
  None` check (the two are explicitly linked above, "should be decided
  together"). FILES' `'*'`-traversal `:manifest()` rejection (this
  session's other two PRs) is the SAME question at one more remove
  (GROUP mode there also produces one candidate per file_home group).

  **Built 2026-10-16, scope: FILES + RESULTS/CSVPATHS audited together**
  (David's call — "closes the whole cross-datatype question in one
  pass" over a FILES-only fix). The audit found RESULTS/CSVPATHS were
  *already* fixed (`ResultsReferenceFinder3._star_group_and_reduce()`
  was converted to the exact partition-aware shape on 2026-09-28,
  confirmed live by reading its own current docstring/code — this
  bucket-list entry's "still an unconditional raise" text above was
  stale, not a live gap) — only FILES itself still had the naive count
  check. Two sites fixed on branch `fix/star-traversal-partition-aware-
  content-read`:
  - `query()`'s literal-root GROUP-mode branch: removed the
    `partitioned and pointers and has_manifest and not has_field_function`
    unconditional raise entirely (the reduction logic right below it
    already does the correct thing once nothing blocks it from running);
    `ambiguous_content_read`'s own computation gained `and not
    (partitioned and pointers)`.
  - `_query_star_traversal()`'s GROUP-mode branch (`:all()`/`:groups()`
    across every named-file): its `ambiguous_content_read` computation
    gained `and not partitioned` (pointer presence already guaranteed by
    this point in the method, unlike the literal-root case above).
  Tests updated: `TestAllForOneNamedFile::test_all_combined_with_
  manifest_now_resolves_each_groups_own_entry` (was `..._is_not_yet_
  supported`), `TestGroupsForOneNamedFile::test_groups_combined_with_
  manifest_now_resolves_each_groups_own_entry` (same), `TestStarTraversal
  Group::test_all_combined_with_manifest_now_resolves_each_groups_own_
  entry` (was `..._query_succeeds_resolve_raises`), `TestStarTraversal
  GroupsAnyDepth::test_combining_with_manifest_now_resolves_each_groups_
  own_entry` (same) — all four now assert a successful `.resolve()`
  giving each group's own manifest entry, `ambiguous_content_read is
  False`, instead of a raise. Full `tests/references/` suite: 1631
  passed (no net test-count change — four tests converted in place, not
  added). Full local-backend suite: 4092 passed, 11 failed (the same
  known SFTP/S3 baseline, unrelated).

## Predicate-argument field accessors (`:on_arrival(:not_none())`) — ALL THREE PIECES NOW BUILT 2026-10-17

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

- **The generic "any field accessor takes a predicate argument"
  mechanism — BUILT 2026-10-17**, closing this entry's own original
  motivating worked example: `$*.files.:home():definition(:on_arrival
  (:not_none()))` — "which named-files have on_arrival set." David,
  2026-10-17, confirming the open interpretive question: a surviving
  named-file's own FULL `definition.json` content is what the reference
  resolves to (not just the `on_arrival` value, and not just a bare list
  of names) — "I'm not going to try to recreate my state of mind when we
  did that example, but in the moment I agree with you."

  No new declarative class attribute needed (deliberately NOT a
  `SELECTOR_WHEN_ARGUED`-style flag) -- the mechanism is a plain
  `isinstance(arg, PredicateFunction3)` type check, which is already
  generic by construction: any current or future field accessor that
  widens its own `ARG_TYPES` to include `PredicateFunction3` works here
  for free, no finder-side change needed per function. Implementation:
  - `OnArrival3.ARG_TYPES` widened from `()` to `(PredicateFunction3,)`.
  - `Definition3.ARG_TYPES` widened from `()` to `(Function3,)` (any
    nested field accessor, syntactically) -- `Definition3.check_valid()`
    overridden to cross-validate it: must be `SOURCE == "definition"`
    AND its own arg must be a `PredicateFunction3`, else a clear raise
    (not a confusing downstream failure).
  - `FilesReferenceFinder3._chained_definition_call()` widened to no
    longer require `call.arg is None` (it used to only recognize the
    BARE `:home():definition()` shape).
  - `_query_star_traversal()`'s own `is_home and definition_call is not
    None` branch, once the candidates are already narrowed to zero-level
    registrations, additionally drops any candidate whose own
    `describer.get_config(name)` field (read via the SAME `KEY`-driven
    extraction the ordinary bare-field-accessor read already uses, see
    new `_matches_definition_field_predicate()`) fails the nested
    predicate -- before building results, so everything downstream
    (resolving `definition.json`'s content for survivors) is unchanged.
  - **A real regression caught and fixed before shipping, not after**:
    `resolve_kind` classifies this whole reference as `METADATA_FIELD`
    (a nested `SOURCE == "definition"` call triggers the same default
    rule an ordinary bare field read does), not `METADATA_FILE`. First
    attempt widened `_extract_data()`'s own `kind == METADATA_FILE`
    guard to also admit `METADATA_FIELD` (mirroring the analogous,
    already-shipped widening for RESULTS' `:errors():idchain(...)` GATE)
    -- confirmed LIVE this was unsafe for FILES specifically: it let
    ORDINARY field reads during `'*'` traversal (e.g.
    `:all():last():uuid()`, already `METADATA_FIELD` by `resolve_kind`)
    also reach that block, where Rule 1b's own unconditional "`Star3`
    root_major + `result.uuid is not None`" re-derive-by-uuid branch
    incorrectly intercepted them, returning the whole manifest entry
    instead of the `uuid` field value -- 9 tests caught this
    immediately. Fixed by checking `_chained_definition_call()`
    directly, BEFORE `resolve_kind` is even read (alongside the existing
    `_bare_log_call` check), rather than touching the `kind ==
    METADATA_FILE` guard at all. Lesson: the RESULTS widening being safe
    does not mean the identical-looking FILES widening is safe too --
    each finder's own `_extract_data()` has different branches with
    different implicit assumptions; verify live per finder, not by
    analogy.

  Tests: new `TestPredicateArgumentFiltering` in
  `tests/references/functions/well_known_files/test_definition_3.py`
  (`Definition3.check_valid()`'s own cross-validation); new tests in
  `tests/references/functions/fields/test_on_arrival_3.py`; new tests in
  `TestStarTraversalDefinition`
  (`tests/references/test_files_reference_finder_3.py`), including an
  end-to-end one resolving a real on-disk `definition.json` for the
  surviving candidate -- required widening that test file's own
  `_FakeFileManager`/`_finder()` test harness with a new, optional
  `definitions: dict[name, dict]` parameter (a new
  `_PerNameFakeFileDescriber`), since the existing `_FakeFileDescriber`
  only ever supported one single, global definition dict, not a
  different one per named-file (needed here to prove the filter
  actually filters). Full `tests/references/` suite: 1728 passed (up
  from 1713). Full local-backend suite: 4189 passed, 11 failed (known
  SFTP/S3 credential baseline, unrelated).

- **The GATE dispatch mechanism — BUILT 2026-10-17**, scoped exactly to
  the compendium's own settled acceptance criteria (§4.13/4.14, five
  references using `:idchain()` for both positions) rather than the
  fully-generic mechanism above — turned out NOT to need the generic
  "any field accessor takes a predicate" design at all, since it is a
  single, narrow, already-settled shape (`:errors():idchain(...)`,
  chained, not nested), not an open question. Implementation:
  `ResultsReferenceFinder3._name_three_selector()` gained a 6th return
  value, `gate_call` — recognizes a SEPARATE `Idchain3` sibling in the
  same `name_three` func_chain (distinct from the pre-existing, nested
  FILTER shape, which never reaches this dispatch loop at all — it is
  `accessor.arg`, not its own chain entry), and raises if `:idchain()`
  appears without a preceding content accessor (e.g. `:errors()`) to
  gate. `_extract_data()` reads the (already-existing) `_read_accessor()`
  content UNFILTERED (since the gate's own `:idchain()` call rides as a
  bare sibling, `accessor.arg` stays `None`, so the pre-existing filter
  logic never triggers) and passes it to a new `_apply_errors_gate()`:
  returns the whole, unfiltered content if ANY entry's own "source"
  field matches the gate's predicate, else `None` (not an empty list —
  a failed gate means nothing to resolve at all, same "genuinely
  optional" treatment every other well-known-file miss gets). No change
  needed to `Reference3.resolve_kind()` — it classifies this shape as
  METADATA_FIELD (since the sibling `Idchain3`'s own `RESOLVES_AS`
  override matches regardless of chain position), but `_extract_data()`
  already treats METADATA_FILE/METADATA_FIELD identically at this
  branch and defers the real distinction to `accessor`/`field_call`/
  `gate_call`, so the mischaracterization is harmless. Scoped to
  `:idchain()` only, matching the compendium's own examples exactly, not
  `:message()` (built 2026-10-17, PR #385, not yet merged as of this
  writing) — extending the gate position to `:message()` too is a
  natural, low-risk follow-up once that PR lands (same `matches()`
  interface, same shape, just keyed on "message" instead of "source").
  Tests: new `TestErrorsIdchainGate` in
  `tests/references/test_results_reference_finder_3.py`, covering all
  five compendium examples plus the "no errors.json at all" and
  "`:idchain()` alone, no accessor" rejection cases. Full
  `tests/references/` suite: 1704 passed. Full local-backend suite:
  4165 passed, 11 failed (known SFTP/S3 credential baseline,
  unrelated).

## `:count()` as a whole-array aggregate GATE, and `:above()`'s dual role as range-bound/predicate — BUILT 2026-10-17

The last of the 7 deliberately-deferred items (compendium normative
examples 489-491): `:errors(:count(:above(10)))`, "find csvpaths
generating more than 10 errors." Previously described as "tied to the
predicate-argument GATE mechanism, same prerequisite as `:on_arrival(
:not_none())`" — turned out NOT true once actually traced through the
code: `:count()` tests an AGGREGATE (array length), not a per-candidate
field value, and needed its own design, its own new function, AND
surfaced three more existing-behavior gaps that had nothing to do with
`:count()` specifically. Four pieces, in the order they were found:

**1. A corrected "naming collision" claim.** First pass flagged
`:above()` (needed here as a numeric PREDICATE, "count > 10") as
colliding with `:above()` already registered as an alias of `:after()`
(a RANGE/direction `CONTEXT_SETTER`, PR #379) — David pushed back
("they were intended to just be aliases for the same functionality, is
that not possible?") and was right. There was no collision:
`reference_function_factory_3.py`'s `"above": After3` is a plain dict
alias to the one class, not a competing registration. `After3`'s own
comparison logic (previously only exposed via `_apply_date_range()`'s
internal list-filtering) already encoded "greater than" as its one
semantic — it just needed a `matches(self, value)` method generalizing
that comparison to any orderable value (ints included), and `After3`
now extends `PredicateFunction3` directly (not `Function3`) instead of
multiple-inheriting, since `PredicateFunction3` already IS a `Function3`
subclass — one class, two roles, "position decides meaning" again: as a
range bound it still goes through `_apply_range()`/`_apply_date_range()`
unchanged; nested inside `:count()` it goes through `matches()` instead.
Lesson folded into `feedback_verify_redundancy_claims_live.md` — a third
instance of the same "asserting a conflict without checking the code
first" mistake in two sessions.

**2. `:count()` itself, a new, EXPLICIT exception to nested=FILTER.**
`Count3` (`csvpath/references/functions/filters/count_3.py`) — nested
inside `:errors()`'s own argument, the SAME position `:idchain()`/
`:message()` already occupy as FILTERS, but `:count()` cannot filter
entries at all (an aggregate has no per-entry meaning), so it acts as a
GATE instead, reached from the nested position rather than the chained
one. `ARG_TYPES = (PredicateFunction3,)` (so `:above()`/`:gt()` qualify
for free, same declarative pattern as everywhere else); `matches(data)`
reduces `data` (errors.json's own raw list, or `None`) to `len(data) if
data is not None else 0` and delegates to its own nested predicate.
`Errors3.ARG_TYPES` widened to `(Idchain3, Message3, Count3)`;
`ResultsReferenceFinder3._read_accessor()` gates on it (sets `data =
None` if `accessor.arg.matches(data)` is `False`) alongside the pre-
existing FILTER branches. `Errors3`'s own code comment rewritten to
document all three now-shipped shapes (FILTER/`:idchain()``:message()`,
chained-GATE/`:idchain()`, nested-GATE/`:count()`) as the complete
picture, not two.

**3. The actual blocker: `:all()`/accessor pooling was unconditionally
rejected.** Both normative-example lines need `match_all` (every
instance in a run) combined with a content accessor (`:errors()`) --
`query()` had an immediate, unconditional rejection for exactly this
combination, with its own comment explicitly anticipating this moment
("no established case needs this... left as-is rather than widened
speculatively"). Relaxed to the SAME deferred `ambiguous_content_read`/
Rule-1 pattern `_query_star_traversal`'s own pooling tail
(`_star_pool_and_reduce`) already used for the identical combination
reached via `'*'`-root traversal — not new invention, closing a parity
gap between the two dispatch trees. `query()` now pools every instance
(flagged `ambiguous_content_read` when more than one comes back);
`.resolve()`/`resolve_from()` still refuse to read more than one whole-
resource accessor at once (Rule 1, unchanged) — a caller finds which
instances qualify by resolving them one at a time. Also fixed, for
correctness rather than because this example needed it: both `query()`
and `_star_pool_and_reduce()` computed `ambiguous_content_read` from the
candidate RUN count (`len(selected_runs)`/`len(run_homes)`), which
can't see `match_all` expanding ONE run into several instances — changed
to compute from the actual built `results` list length instead, in both
places. `_query_star_traversal`'s OWN parallel rejection (line ~740,
`'*'`-root traversal specifically) was deliberately left exactly as-is
— no worked example needs it relaxed yet, and `_star_group_and_reduce`'s
own correctness reasoning currently depends on it staying a hard block
— its own comment, and `_star_group_and_reduce`'s, updated to stop
claiming symmetry with `query()`'s now-different check.

**4. Two general `name_three` parsing rules, surfaced by this example,
unrelated to `:count()` itself.** Initially proposed (wrongly) that
normative-examples line 490 was a spec typo to delete — David checked
the compendium directly and caught the correction: both lines exercise
already-documented, GENERAL rules, not a one-off:
- Compendium 4.2b/4.3a + normative examples 393-404: `:all()` and a
  literal `*` are flatly equivalent in `name_three`. `_name_three_
  selector()` used to unconditionally reject a `Star3` body ("use
  :all() instead") — now folds it into the same `match_all` flag,
  raising only if BOTH an explicit `*` and `:all()` are present
  together (two wildcards).
- Compendium 3.19b: "When `name_three` is solely one or more functions,
  a `*` is implied." `_name_three_selector()` used to unconditionally
  reject a bare accessor/field-call with no identity/`:all()`/range
  riding alongside it — now implies `match_all = True` instead, exactly
  when `name_three.functions` is non-empty (by this point any
  unrecognized function has already raised, so non-empty here always
  means a real accessor/field_call survived).

**Tests**: `tests/references/functions/selectors/test_after_3.py`
(`matches()`, `PredicateFunction3` isinstance), new
`tests/references/functions/filters/test_count_3.py`,
`test_errors_3.py` (Count3 as a valid nested arg),
`TestErrorsCountGate` in `test_results_reference_finder_3.py` (both
normative-example forms, explicit-identity gate pass/fail, missing-file,
filter-shape-unaffected), plus three rewritten `TestScopeLimits`/
`TestWellKnownFileAccessors` tests that previously asserted the now-
intentionally-changed rejections. Full `tests/references/` suite: 1741
passed (up from 1721). Full local-backend suite: 4202 passed, 11 failed
(known SFTP/S3 credential baseline, unrelated).

With this, all 7 of the originally deliberately-deferred items are
either built (this one and the generic predicate-argument mechanism) or
correctly re-confirmed as still blocked (the 3 spec-blocked items) or
downgraded to "no driving use case" (FILES' broader `name_one.functions`
generalization) — see `project_references_v3_remaining_scope.md` for the
up-to-date summary David asked to be kept current without re-deriving.

## `$name.files.:manifest():last()` (ordinal pointer into a single named-file's own manifest) — BUILT 2026-10-16

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

Open question David flagged, settled 2026-10-15/16 after two rounds of
careful pushback (see `deferred_work_done_list.md` for the full back-and-
forth): David's own corrected reasoning won out over my initial "leave it
unsupported, `*` + `:flatten()` already covers it" recommendation — (a)
`*` is a one-segment wildcard, so the real workaround would be the much
clumsier `$a.files.:flatten():last().:manifest()`, not a one-segment `*`;
(b) `:manifest()`/`:definition()` are already-established non-path special
cases for FILES, and CSVPATHS/RESULTS already support this exact bare
`:manifest()`+pointer shape natively — so building it closes a genuine
consistency gap, not a new design risk. David: "Yes, please do."

**A real design trap caught 2026-10-15, before building, not after**: David
spotted that this fix would collide with compendium 3.9c's own implied-`*`
rule if built carelessly. `:manifest()` is explicitly listed in 3.9c's
"doesn't operate in a path segment at all" exemption category — it must
NEVER trigger implied-`*`. If it did, `$acme.files.:manifest():last()`
would get silently read as `$acme.files.*:manifest():last()` — a POOLED
match across every `file_home` under `acme`, time-sorted, reduced by
`:last()` — a genuinely different operation from "ordinal-index acme's own
manifest.json array directly" (Rule 1b's actual intent). David's own
worked-out proof: that pooled reading would make `$acme.files.:manifest()
:last()` compositionally a member of the set `{$acme.files.<X>:manifest()
:last() : X ranges over every distinct file_home}` — reintroducing exactly
the "which file" ambiguity Rule 1b exists to bypass.

Live-verified the live blast radius before concluding anything: FILES has
NO implied-`*` wiring at all today (`_apply_implied_star()` is RESULTS-
only, see the done-list entry), so this exact collision cannot happen in
current code. But checking RESULTS' own, already-shipped implementation
surfaced a real, if currently harmless, gap: `$acme.results.:manifest()
:last()` DOES get normalized through `_apply_implied_star()` today
(confirmed live), and `"manifest"` was never actually in that method's own
exemption list — it only avoided breaking anything by accident, because
RESULTS' `:manifest()` always means "whichever run the rest of the chain
already selected, give its manifest" (one run, one manifest.json file, no
shared-array-across-candidates concept the way FILES' Table 1 has).
**Fixed 2026-10-15**, see `deferred_work_done_list.md` — `"manifest"`
added explicitly to `_apply_implied_star()`'s exemption list, with a test
proving a prefixed `:manifest()`+pointer selects directly rather than
pooling across prefixes.

**Built 2026-10-16**: the actual Rule 1b extension (the symmetry David
originally asked about), on branch `feature/references-v3-manifest-last-
symmetry`. It is its own narrow, early-intercepting special case in
`query()` — a new `_pointer_before_manifest(reference, "manifest")` check
placed right after the existing bare `:manifest():<field>()` branch and
before the generic "functions attached directly to name_one" rejection —
exactly like Rule 1a/1b's own dedicated `Star3` check already is, and
never something implied-`*` could re-route through (FILES still has no
implied-`*` wiring at all, and `:manifest()` is its own named exemption
regardless, see above). Selects one entry out of
`file_manager.get_manifest(root_major)` (this named-file's own manifest,
not the global ledger) via the same shared `_apply_pointer()` Rule 1b
already uses; `_extract_data()` mirrors Rule 1b's own re-derive-by-uuid
pattern, scoped to the same per-named-file manifest. See
`deferred_work_done_list.md` for the full implementation note and tests.

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

## Grammar / argument-type gaps — ALL BUILT, kept as a historical record

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

## `'*'` traversal — RESULTS/CSVPATHS remaining gap — all but one item BUILT, `:groups()`+`'*'` semantics still design-blocked

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

## `'*'` traversal — FILES — all items BUILT except the predicate itself (`:on_arrival(:not_none())`, design-blocked on the generic predicate-argument mechanism above)

- `FilesReferenceFinder3`'s own `_query_star_traversal()` combining `'*'`
  traversal with a field accessor riding beside the pointer in
  `name_three` (POOL and GROUP modes alike) — **BUILT 2026-08-29**, see
  `deferred_work_done_list.md`. `:manifest()` (whole-resource) used to
  stay rejected here deliberately (GROUP mode can legitimately produce
  more than one reduced candidate, and this method set no
  `ambiguous_content_read` flag to catch resolving several whole entries
  at once) — **that flag is now partition-aware, BUILT 2026-10-16**, see
  this list's own "'*'-traversal content-accessor guards" entry above
  and the done-list's matching writeup. `:manifest()` combined with
  GROUP modes during `'*'` traversal now resolves correctly instead of
  being flagged ambiguous.

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
  with GROUP modes used to stay rejected, unchanged by this fix — **now
  also BUILT, 2026-10-16**, same partition-aware fix referenced above
  (this was the literal-root twin of that same gap).
- A literal prefix *before* `:flatten()` for FILES — **BUILT 2026-08-27**,
  see `deferred_work_done_list.md`.
- FILES' `:from()`/`:to()` combined with `:all()`/`:groups()` grouping in
  name_one — **error message fixed 2026-09-25**, see
  `deferred_work_done_list.md`. Already correctly rejected (not a silent
  misbehavior) but the raise was merged into the `:manifest()` check just
  below it, giving a confusing "combining with `:manifest()`" message even
  when no `:manifest()` was present — split into its own check with an
  accurate message. The underlying rejection itself stays exactly as
  intentional as it always was (genuinely ambiguous whether a range means
  "last N overall" or "last N per group," same reasoning as RESULTS' own
  identical rejection) — not attempting the actual per-group range logic,
  only the error message was wrong.
- A literal name_three body for FILES (bypassing a pointer function
  entirely) — **BUILT 2026-09-22**, see `deferred_work_done_list.md`.

## Functions

- Functions named in the spec/example-queries docs with no `Function3`
  subclass yet: `:count()`, `:has_errors()`. **Both BUILT now (2026-10-
  17/18 respectively) -- this line is historical, kept for the dated
  correction trail below, not current status.** (Corrected 2026-08-26:
  `:type()` used to be listed here too, but it was built as part of the
  Table 1 field-accessor batch — confirmed live, `Type3` is registered,
  `NAME = "type"` — this list had gone stale; removed. Corrected again
  2026-08-27: `:yesterday()` was also stale — confirmed live,
  `Yesterday3` is registered, built alongside `:today()` in the "pure
  value" date/time functions batch — removed. Corrected again
  2026-09-21: `:before()`/`:after()`/`:above()` moved out — see the
  "Direction/ordinal functions" entry, now BUILT. Corrected again
  2026-10-16: `:quarter()`, `:choice()`, `:names()`, `:at()` all moved
  out — see the four dedicated entries below, each a considered
  rejection, not an oversight. Corrected again 2026-10-17: `:message()`
  moved out — **BUILT**, see below.)

  - `:message()` — **BUILT 2026-10-17.** `normative_reference_
    examples.txt` uses it as `:errors(:message(/customer: 319/))`,
    directly beside the already-built `:idchain()`'s own
    `:errors(:idchain("..."))` — same shape, same mechanism, just
    keyed on the error entry's own "message" field (confirmed real
    against `Error.to_json()`) instead of "source". Built as a near-
    exact copy of `Idchain3` (`csvpath/references/functions/filters/
    message_3.py`) — same `ARG_TYPES`/`RESOLVES_AS`/`matches()` shape —
    plus `Message3` added alongside `Idchain3` in `Errors3.ARG_TYPES`
    and in `ResultsReferenceFinder3._read_accessor()`'s own filtering
    branch. Tests: `tests/references/functions/filters/test_message_3.py`
    (unit, mirroring `test_idchain_3.py`) and four new integration
    tests in `TestWellKnownFileAccessors` (exact-string, regex,
    `:not_none()`, no-match-is-a-legitimate-empty-list). Full
    `tests/references/` suite: 1713 passed (up from 1697).
  - **`:has_errors()` — BUILT 2026-10-18.** The 2026-10-17 re-audit above
    correctly found no SETTLED worked example anywhere (every citation
    was draft/WIP) -- that was still true the day this was built; David
    instead gave the semantics directly: "mirror `csvpath.managers.
    results.result.Result.has_errors()`" (literally `self.errors_count
    > 0`), plus the concrete goal ("filter or resolve items that have
    errors, or that don't, without having to use the errors count with
    boolean logic"), which is its own worked-example-equivalent. David
    also raised a real, separate question while scoping this: whether
    `error_count` even exists on the RESULT INSTANCE manifest at all (he
    had looked at a running FlightPath Data and not seen it, and
    believed it wasn't there) -- checked `result_registrar.py` directly
    rather than assume either way: it IS written there (`mdata.
    error_count = self.result.errors_count`, then `m["error_count"] =
    mdata.error_count`, unconditional), confirmed by David independently
    checking the same registrar himself.

    **A real, separate, previously-undetected bug surfaced by that
    check**: `ErrorCount3` (`:error_count()`) only exposed the RUN-level
    copy of this same field -- its own code comment claimed "no
    equivalent per-instance field... confirmed against
    result_registrar.py," which was simply wrong, contradicted by that
    very file. The spec doc (`references_v3_required_manifest_
    functions.md`, table 6) had the identical gap -- `error_count`
    documented in table 5 (Run Manifest) but missing from table 6
    (Result Instance Manifest) even though the field is written there
    too. This also meant TWO ALREADY-NORMATIVE worked examples in
    `normative_reference_examples.txt` (`$alpha.results.:flatten():
    first().:all():error_count()` and the `:index(5)` sibling right
    after it, both name_three/instance-level) were unsatisfiable before
    today -- `ErrorCount3`'s own `POSITIONS` only allowed `NAME_ONE`,
    so these would have raised "`:error_count()` is not legal at
    `name_three` for results," not just returned wrong data. Fixed
    alongside `:has_errors()` (same root class, directly adjacent, David
    confirmed "please proceed, including the `ErrorCount3` fix") --
    `KEY`/`POSITIONS` widened to the same dual run/instance shape
    `Time3` already established. Confirmed live, not just fixed and
    assumed: both previously-broken normative examples now resolve
    correctly.

    **Implementation**: `HasErrors3` (`csvpath/references/functions/
    fields/has_errors_3.py`) -- a plain `SOURCE == "manifest"` field
    accessor reading the SAME `"error_count"` key `ErrorCount3` does
    (both run and instance level), NOT built as sugar for `:errors(
    :count(:above(0)))` despite the two being semantically equivalent
    (same underlying `Error` collection, two different persisted
    representations) -- that composition is exactly the "errors count
    with boolean logic" David asked not to have to write. One new,
    small, generic piece needed: every existing field accessor before
    this returned its raw manifest value verbatim (confirmed -- no
    function anywhere post-processed its own value). Added `Function3.
    transform_value(value)` (a classmethod, not an instance method --
    a finder's own field-accessor dispatch only ever has the registered
    CLASS at this point, from `ReferenceFunctionFactory.get_registered_
    class()`, never a built instance; default is a no-op/identity, so
    every existing field accessor is unaffected without its own
    override); `HasErrors3` overrides it to reduce the raw int to a
    bool. Wired into all three of `ResultsReferenceFinder3._extract_
    data()`'s own field-extraction call sites (run-level via
    `:manifest()`, run-level direct, instance-level).

    **The adjacent `:error_count()` predicate-argument gap flagged here
    -- BUILT 2026-10-18, separate branch/PR, same day.** David asked
    for it explicitly once he understood the gap ("thank you, that
    helps... yes, please build it"), after a first explanation that
    didn't land -- re-explained with a concrete before/after pair
    (`:error_count()` bare, reading one already-selected entity's own
    count, vs. `:error_count(:above(3))` GATING a pooled list by that
    same count) rather than the mechanism-first framing that didn't.
    `ErrorCount3.ARG_TYPES` widened from `()` to `(int,
    PredicateFunction3)` -- a bare int (`:error_count(0)`) is an exact-
    match test, no dedicated predicate class needed for it.
    `:below()`/`:lt()` (`Before3`) needed the SAME dual-role treatment
    `:above()`/`:gt()` (`After3`) already got for `:count()` --
    extends `PredicateFunction3` now too, with its own `matches()`
    (strictly-less-than, mirroring `After3`'s strictly-greater-than,
    including the same clear rejection of a nonsensical
    `TimeWindowFunction3` bound).

    New shared `ResultsReferenceFinder3._matches_field_predicate(value,
    arg)` (a `PredicateFunction3` arg delegates to its own `matches()`;
    a bare leaf value is an exact-match test) and `_run_field_value(
    run_dir, field_call)` (reads a run's own manifest field, running it
    through `transform_value()` for consistency with however the same
    field actually resolves). Wired into THREE places, since the GATE
    needs to apply wherever a pooled candidate list is assembled, not
    just where one is finally resolved: `query()`'s own literal-root
    candidate-finalization (right alongside `:having()`'s own copy of
    this same filter-then-pool pattern), and BOTH of `_query_star_
    traversal()`'s shared tails (`_star_pool_and_reduce()`/`_star_
    group_and_reduce()`) for the `'*'`-root case -- required widening
    `_star_run_selector_chain()`'s own return tuple (4 values -> 5,
    adding `field_call`) and updating all four of its call sites. A
    no-op whenever the field accessor carries no argument at all (an
    ordinary bare field read, e.g. `:uuid()`, unaffected -- confirmed
    by a dedicated test).

    **Tests**: `TestErrorCountPredicateGate` in `test_results_
    reference_finder_3.py` -- all three normative-example forms
    (`:above()`/`:below()`/bare-int-exact-match), confirmed equivalent
    to each other where the doc says so, BOTH the `'*'`-root and
    literal-root forms (the normative doc only shows `'*'`-root, the
    literal-root path is the same shared mechanism, confirmed live not
    assumed), and the bare-no-predicate no-op case. `TestMatchesField
    Predicate` for the shared helper directly. `Before3`'s own new
    `matches()` (mirroring `test_after_3.py`'s own `TestMatches`
    exactly). `tests/references/`: 1814 passed (up from 1800). Full
    local-backend suite: 4275 passed, 11 failed (known SFTP/S3
    credential baseline, unrelated).

    **Tests**: `tests/references/functions/fields/test_has_errors_3.py`
    (metadata, `transform_value()` unit tests), `test_error_count_3.py`
    updated for the widened `KEY`/`POSITIONS`, `TestTransformValue` added
    to `tests/references/functions/test_function_3.py` (the generic
    hook's own default-identity behavior), plus new integration tests
    in `test_results_reference_finder_3.py` (run/instance scope for
    both functions, the previously-broken `:all():error_count()`/
    `:all():has_errors()` pooled shape, missing-field-is-`False`). Full
    `tests/references/` suite: 1800 passed (up from 1789). Full local-
    backend suite: 4261 passed, 11 failed (known SFTP/S3 credential
    baseline, unrelated).
  - `:count()` — **BUILT 2026-10-17.** Was previously described here as
    "tied to the predicate-argument GATE mechanism, the same unbuilt
    prerequisite as `:on_arrival(:not_none())`" — turned out NOT to be
    true once actually built: `:count()` operates on the LENGTH of
    errors.json (aggregate count-then-compare), a genuinely different
    mechanism from the per-candidate field-value filtering the FILES
    `:on_arrival()` work built, and needed its own separate design in
    `ResultsReferenceFinder3`. See the new, dedicated "`:count()` /
    `:above()` as a dual-role predicate" entry below for the full build
    (and the `:above()` "naming collision" correction David caught —
    there was no collision at all).

- **`:quarter()` — deliberately NOT building, decided 2026-10-16, removed
  from the list above.** David: it is "both easy and suspect" — trivial to
  implement, but we do not actually know that "Q2"-style quarter labeling
  is how everyone would want to indicate a quarter, there is no other
  slam-dunk representation to fall back on either, and there is no
  current demand signal driving it. This is a considered rejection, not
  an oversight — do not resurrect it just because it would be easy.
  `:quarter()` appeared in two places purely as an ILLUSTRATION of "a
  time-component function used as a context setter / dynamic path
  segment," a point `:yesterday()` (already built) makes equally well on
  its own: `creating references v3.txt`'s own raw example list (left
  untouched — historical scratch notes, not revised) and the compendium's
  §6.43 context-setter role-taxonomy example list (`:quarter()` removed
  from that list 2026-10-16, `:yesterday()` carries the illustration
  alone now). If a real demand signal and a settled representation
  (not necessarily "Q2") ever show up, re-add it as its own entry with a
  worked example, same as every other function here.

- **`:choice()` — deliberately NOT building, decided 2026-10-16, removed
  from the list above.** Confirmed live: `:choice()`'s own intent (a
  pipe-delimited list of exact matching names, e.g. `:choice("orders|
  invoices|shipments")`) is fully expressible via the already-built
  `:regex()`, with one caveat David wanted confirmed, not assumed:
  `:regex()`'s own matching is UNANCHORED `re.search()` everywhere in
  this codebase (deliberate, established convention, shared by
  `:idchain()`/`_segment_matches()`/`_matching_names()`), so a bare
  `:regex("orders|invoices|shipments")` would ALSO match a substring
  like "sub_orders_2024" — not quite equivalent on its own. Anchoring it
  (`:regex("^(orders|invoices|shipments)$")`) closes that gap and is
  confirmed live to behave exactly like `:choice()` would have
  (verified with a real `re.search()` comparison: the anchored form
  matches "orders"/"invoices"/"shipments" but not "sub_orders_2024"/
  "invoices_old", the unanchored form matches all five). `:choice()`'s
  own compendium mentions (§3.8's `root_major` function list, §3.9c's
  "fully occupies a path segment" exemption category and its "pattern-
  matching analogs of `:name(...)`" note) are corrected to drop it,
  leaving `:regex()`/`:name()` to cover the same ground. The dead
  `"choice"` entry in `ReferenceFinder3._apply_implied_star()`'s own
  exemption tuple (never reachable — nothing was ever registered under
  that name) is also removed. If a real demand signal shows up later
  (anchored `:regex()` is more cumbersome to write/read than a bare
  pipe list for this one common case), reconsider as a UX-sugar
  function, not a capability gap.

- **`:at()` — deliberately NOT building, decided 2026-10-16, removed
  from the list above.** David: "certainly redundant" — its only
  appearance (`creating references v3.txt`'s `*#my_worksheet.:at(-1)`)
  is exactly what the already-built `:index()` already does. No
  compendium mentions to correct (it was never written up there).

- **`:names()` — deliberately NOT building, decided 2026-10-16, removed
  from the list above.** David's own framing: wanted it as a `**`-style
  analog ("match any number of intermediate segments, then anchor on a
  literal/`*` suffix"), but only if the already-built `:flatten()`
  prefix/suffix mechanism could not already do the same thing. Confirmed
  LIVE it already can, including a MULTI-segment suffix (not just a
  single trailing segment) — `_candidates_for_name_by_prefix_and_suffix()`
  compiles both the prefix and suffix through the same general
  `_compile_path_pattern()` used everywhere else, with no length limit on
  either side. Live repro: a fixture with `vault/b/c/one.csv` (zero-
  segment gap) and `vault/b/mid/c/two.csv` (one-segment gap), queried as
  `$vault.files.b/:flatten()/c/*.:last()` (the pointer has to sit in
  name_three via a dot, not bare `*:last()` in name_one — FILES still
  does not support functions attached directly to name_one, see the
  implied-`*` entry above) — correctly matched both and `:last()`
  correctly picked the array-order-last one; a mismatched prefix, a
  mismatched suffix shape, and a too-long non-matching suffix were all
  correctly excluded. `:names()` was never written up in the compendium
  (only two raw lines in `creating references v3.txt`, left untouched),
  so no spec correction was needed there, just the "Functions" list
  above.

## Direction/ordinal functions (`:before()`/`:after()` and their word aliases) — BUILT 2026-10-16

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

**Built 2026-10-16**, branch `feature/references-v3-direction-functions`.
Two decisions settled with David first (see `deferred_work_done_list.md`
for the full back-and-forth):

1. **A real spec inconsistency caught before building, not after**: 6.28d's
   own worked example ("find versions... from the beginning of 2026
   through yesterday") used `:after(:date("2026-01-01"))`, but 6.28b's
   alias table defines `:after()` as strictly EXCLUSIVE (greater-than) --
   "from the beginning of 2026" is an INCLUSIVE claim, which is `:from()`'s
   meaning, not `:after()`'s. Resolved: the alias table is authoritative,
   the example was wrong -- fixed to `:from(:date("2026-01-01"))`
   (`references_v3_compendium.md` 6.28d).
2. **Alias rollout scope**: ship the full 9-name table now (`before`/
   `below`/`lt`; `after`/`above`/`gt`; plus `lte`→`:to()`, `gte`→`:from()`
   as new aliases on the EXISTING classes), not just the 2 primary names --
   cheap once `Before3`/`After3` exist (each alias is a one-line registry
   entry).
3. **Alias mechanism**: a second `ReferenceFunctionFactory._FUNCTIONS`
   dict key pointing at the SAME class, not a separate class or a new
   registry mechanism -- `Function3.name` already returns `self.NAME` (a
   class constant), so a built instance's `.name` always reads back as
   the canonical form regardless of which alias key reached it, with zero
   extra plumbing needed anywhere that already branches on `.name`.

Implementation: `Before3`/`After3` (new, `csvpath/references/functions/
selectors/before_3.py`/`after_3.py`), same `POSITIONS`/`DATATYPES`/
`ARG_TYPES` shape as `From3`/`To3`. The real work was generalizing the
shared range mechanism on `ReferenceFinder3` (`_range_calls_from_built()`
-- new, finds the lower/upper bound call and enforces 6.28c's "same
direction twice is illegal" rule; `_apply_range()`/`_slice_by_position()`
-- now take an `end_inclusive` flag; `_apply_manifest_date_range()` -- now
takes raw calls instead of pre-resolved date strings, reads inclusivity
off each one's own `.name`) and rewiring all ~7 call sites across the
three finders (FILES' name_three range; CSVPATHS' name_one version range
and name_three identity-mode range, including the exclusive-bound
adjustment applying AFTER identity-to-position resolution; RESULTS' run-
level range, run-level date range via its own separate `_apply_date_range`,
and statement-level range) to use the shared lookup instead of a hand-
written `from_call = next(f for f in built if f.name == "from")`.

A secondary fix needed along the way: `Function3Describer.describe()`
gained an optional `name` override parameter so `describe_all()` can give
each alias its own correctly-headed/anchored markdown block (aliases are
registered as extra dict keys pointing at the same class, so without the
override every alias would silently describe itself as its canonical
name, breaking `describe_all()`'s own "index and blocks agree on function
count" test invariant).

Tests: new `test_before_3.py`/`test_after_3.py` (metadata, arg validation,
alias resolution, canonical-name-on-build), plus new direction-function
test classes in all three finder test files exercising index-mode,
date-mode, exclusive-bound edge cases (negative indices, identity-mode
resolution order), dissimilar-direction pairing, same-direction rejection,
and alias equivalence. Full `tests/references/` suite: 1693 passed (up
from 1631). Full local-backend suite: 4154 passed, 11 failed (the known
SFTP/S3 credential baseline, unrelated).

## Bigger, standing items — type-ahead and production-wiring PERMANENTLY SET ASIDE for CsvPath Framework's own v3 release, 2026-10-17

David, 2026-10-17: wiring references-v3 into the main CsvPath Framework
codebase, and type-ahead, are both out of scope for CsvPath Framework's
own v3 release -- not abandoned, just not v3's first use case. The actual
first use case is agents querying the environment *without* the
environment itself using v3 internally. Both belong to the FlightPath
products instead (production-wiring to FlightPath Generator/Server/Data
generally; type-ahead specifically to FlightPath Data), picked up
individually once those products are worked on. CsvPath Framework ships
its v3 MVP before any FlightPath product uses it. Do not treat either
item below as a blocker to calling v3 done/released.

- **Type-ahead.** A prototype exists (`specs/references_v3/notes/
  autocomplete_prototype.py`) demonstrating the intended mechanism (Lark
  `parse_interactive()`/`InteractiveParser.choices()` plus a datatype/slot-
  filtered function registry), but it predates the merged grammar and
  isn't wired into `REFERENCE_GRAMMAR_3`/`Function3`/`describe()` at all.
  Deferred to FlightPath Data.
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
  Deferred to FlightPath Generator/Server/Data, per-product.

## The remaining 7 deliberate deferrals — dependency structure settled 2026-10-17

With the two items above set aside, 7 items remain on this list, each a
deliberate (not forgotten) deferral. 3 are blocked on David writing/
settling more spec (no worked example exists yet); 4 just need a branch
and design exploration (spec intent already given, only the code
mechanism is undesigned) -- but those 4 are not flat/independent: 2 are
roots, 2 ride along behind one of them. Full detail lives with each
item's own entry elsewhere in this file; this is the cross-reference so
the shape doesn't need re-deriving:

- **Spec-blocked** (independent of each other and of everything else):
  `:groups()`+`'*'` traversal for RESULTS; the cross-datatype "select by
  uuid"+set-operations item (Function self-documentation section); and
  `:has_errors()` (Functions section).
- **Design-needed, INDEPENDENT roots**: the generic predicate-argument
  mechanism (`:on_arrival(:not_none())`, this file's own dedicated entry
  above) and time-component context setters (this file's own dedicated
  entry) -- these two are NOT tied to each other; different mechanisms
  entirely.
- **Design-needed, DEPENDENT on the predicate-argument mechanism**:
  FILES' broader `name_one.functions` generalization (its only-ever-
  cited worked example itself needs the predicate mechanism) and
  `:count()` (explicitly the same gate prerequisite).

David's own call, 2026-10-17: start with the generic predicate-argument
mechanism, since it unlocks the two dependent items as a side effect.

**SUPERSEDED, 2026-10-18 — this whole cross-reference is now historical.**
The predicate-argument mechanism and time-component context setters were
both built 2026-10-17 (own dedicated entries above); `:count()` was also
built that same day, confirmed NOT actually dependent on the predicate
mechanism after all (a separate, aggregate-length mechanism); the FILES
`name_one.functions` generalization was re-assessed and downgraded to "no
driving use case" (its only motivating example was satisfied by the
predicate mechanism's own narrower fix). `:has_errors()` was built
2026-10-18 (own dedicated entry above), given concrete semantics directly
by David rather than needing a worked example first. What is left of the
original 7: just 2 of the 3 spec-blocked items (`:groups()`+`'*'`
traversal, the cross-datatype uuid/set-ops item) — `:has_errors()` is
done, not still spec-blocked. See `project_references_v3_remaining_
scope.md` (Claude's own memory, kept current without re-deriving) for the
up-to-date summary.

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
