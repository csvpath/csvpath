# References v3 — Deferred Work Bucket List

A running, flat list of everything punted to a later commit/branch/design
conversation while working on references v3 — the single place to check
"how close are we." Add to this whenever something gets deferred, whether
mid-conversation or mid-code. Remove/check off an item once it's actually
built, rather than leaving it to rot.

## Field-accessor fallback to the global ledger entry — not built, needed for the global-ledger tables

Found 2026-08-25 while starting the deferred global-ledger batch (Tables
2/4/7 of `references_v3_required_manifest_functions.md`). Live-tested
first, not assumed: built a fixture where the global ledger's own entry
for a run said `named_file_name = "LEDGER_VALUE"` and the run's own
manifest said `"RUN_MANIFEST_VALUE"` — both `$*.results.:last():
named_file_name()` and `$acme.results.:last():named_file_name()`
returned the *run's own* value, never the ledger's. Confirmed: **no
existing code path reads a field directly off a Rule-1a/1b-selected
ledger entry** — every field accessor resolves to a real matched entity
and re-reads *that entity's own* manifest.json, regardless of how the
entity was found.

Several Table 2/4/7 fields only exist in the *ledger's* own entries, with
no per-entity equivalent at all (e.g. Table 2's `file_manifest`, a
pointer *from* the ledger entry *to* the named-file's own manifest — the
named-file's own manifest doesn't self-reference this at all, see issue
#261 for the closest related gap; Table 4's `paths_manifest`; Table 7's
`archive_path`/`named_files_root`/`named_paths_root`).

**David, 2026-08-25 — the actual design principle, not a one-off
workaround**: "when we are working with any item (registered, loaded, or
run) we are talking about a single conceptual item that owns all its
data -- if we have to do more work to bring all that data together then
we do, but that is our problem, not the user's problem." So the fix
isn't a narrow `SOURCE="ledger"` mode that only works for the bare
Rule-1a/1b shape — it's a general fallback: **any field accessor, for any
matched entity, however it was found, checks the entity's own manifest
first and falls back to that same entity's corresponding global-ledger
entry (looked up by uuid) if the field isn't there.** A caller asking for
`origin_path` on a specific FILES version shouldn't need to know that
field only lives in the global ledger, not the named-file's own
manifest — the finder does that assembly work, not the caller.

Confirmed as the agreed design (not yet built). Needs, before building:
- Extend the shared `_extract_data()`/`_extract_field_value()` path (all
  three finders) with the fallback-to-ledger-entry-by-uuid step.
- A way for a function's `KEY` dict to express *both* the per-entity
  spelling and the ledger's own spelling for the same concept, for the
  cases where they differ (e.g. Table 1's `from` vs. Table 2's
  `origin_path`) — `KEY` alone isn't enough for those; something like a
  parallel `LEDGER_KEY` dict, checked only on fallback, is the likely
  shape but not yet designed in detail.
- This is genuinely cross-cutting (new step in core extraction logic
  shared by all three finders), not "write more field-accessor classes"
  — treat as its own small design/build pass, not folded into the
  ordinary per-table batches.

This unblocks most of the remaining Table 2/4/7 field-accessor work once
built — see the "Field-accessor coverage" entry above for what's already
done and what's still deferred pending this mechanism.
## "Pure value" date/time functions (5.29) — only `:date()` exists, 10 of 11 missing

Found 2026-08-24 (Phase 1 compendium review). The compendium lists eleven
"dumb value-producing functions": `:year()`, `:month()`, `:month_name()`,
`:day()`, `:day_name()`, `:hour()`, `:hour_24()`, `:minute()`, `:second()`,
`:yesterday()`, `:today()`, `:date(...)`. Checked all eleven directly —
only `:date()` is registered. `:yesterday()` was already named individually
in this list's "Functions" section; the other nine were not previously
tracked at all. Note `:date()` doesn't need to expand to cover the others'
jobs — these are genuinely separate, smaller-grained accessors (year vs.
month vs. day-of-week etc.), not overlapping with what `:date()` already
does.

## Predicate support functions (5.31) — only `:having()` exists, 7 of 8 missing

Found 2026-08-24 (Phase 1 compendium review). The compendium lists eight
predicate-support functions: `:true()`, `:false()`, `:none()`,
`:not_none()`, `:empty()`, `:not_empty()`, `:regex(/.../)`, `:having(...)`.
Checked all eight — only `:having()` exists. `:not_none()`/`:regex()` are
already tracked individually elsewhere on this list (the predicate-
argument gate mechanism, and the grammar/argument-type gaps section,
respectively) — not double-counted here. `:true()`/`:false()`/`:none()`/
`:empty()`/`:not_empty()` are new, not previously tracked anywhere.

## `:printouts()` and `:log()` file accessors — not built

Found 2026-08-24 (Phase 1 compendium review, item 5.9). The compendium
lists ten well-known file accessors as "the complete class": `:manifest()`,
`:definition()`, `:data()`, `:errors()`, `:printouts()`, `:vars()`,
`:meta()`, `:unmatched()`, `:file(...)`, `:log()`. Checked all ten directly
against the function registry — eight are real; `:printouts()` and `:log()`
have no `Function3` subclass anywhere. Not previously tracked —
`function_coverage_matrix.md` doesn't mention either name, and neither is
on this list's existing "Functions" section of named-but-unbuilt items.

## `Function3.describe()` has no markdown-rendering capability — 5.4's requirement not met

Found 2026-08-24 (Phase 1 compendium review, item 5.4): "Reference
functions are self-documenting... must be able to output .md in a similar
way to `csvpath/cli/function_describer.py`." Checked `Function3.describe()`
(`function_3.py:120-131`) directly — it exists, but only returns a plain
dict (`name`/`summary`/`role`/`datatypes`), explicitly documented as "what
a future type-ahead layer's registry query is meant to read." It does not
render markdown or any human-readable document, unlike match functions'
own `FunctionDescriber.describe()` (`csvpath/cli/function_describer.py`),
which actually prints/renders formatted (optionally markdown) output. The
underlying structured data `describe()` returns is a reasonable
foundation, but the actual rendering layer 5.4 requires doesn't exist yet.

## Field-accessor coverage against real manifest fields — Phase 2, in progress

Compendium 5.7: "There must be a field accessor function for every field
available in any of the manifest.json files." David pointed to
`specs/references_v3/spec/references_v3_required_manifest_functions.md`
as the final, authoritative spec for exactly this.

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

**Still deferred, not yet built:**
- **The three *global-ledger* tables (2, 4, 7)** — deliberately held back
  from this batch. Several of their fields share a concept with an
  already-built per-entity field but use a *different literal key*
  (e.g. Table 2's `origin_path` vs. Table 1's `from`, both meaning "where
  this came from") — extending an existing function to cover this needs
  the same-datatype-different-key-by-scope mechanism, not just a new
  `KEY` entry. Needs its own pass.
- **`:template()`** — genuinely needs a new mechanism (source picked by
  *position*: bare/no-pointer at name_one reads `definition.json`'s
  default, alongside a real pointer reads that specific version's
  manifest snapshot), plus RESULTS is blocked on a `results_registrar.py`
  schema gap (the run manifest doesn't store its own `template` at all,
  confirmed by David — a core-Framework gap, not something references-v3
  can fix alone). **David, 2026-08-25: the `results_registrar.py` gap is
  explicitly out of scope for now** — sweep up before a full release,
  expected to be low-effort to wire into `:template()` once added
  (the template used to build the run's own directory must already be
  known/available at the same point `results_registrar.py` writes every
  other per-run captured field, e.g. `named_file_size`, so writing one
  more field there should follow the same existing pattern). Not part of
  this batch either way.
- **`sources`/`destinations`/`transfers`/`scripts`/`webhooks` sub-field
  accessors** (Table 8/9) — held pending doc corrections. David fixed
  the webhooks field-name miscopy, the transfers wrong-function-names
  copy-paste, and `destinations.<name>.port`'s host/port mixup — but
  **`sources.<name>.port` still says `:source_host(str)`, not
  `:source_port(str)`** (line 251 as of 2026-08-25) — one more small fix
  needed there before this sub-batch is ready to build.

This is real, ongoing Phase 2 work, not a "someday" placeholder — update
this entry as further batches land.

## `ReferenceExpression3` has no query()-only mode — not built

Found 2026-08-24 (Phase 1 compendium review, item 4.2), which describes
"in some cases a reference expression may combine two references, when
both sets of results are comparable without further resolution." Checked
directly against `reference_expression_3.py`: `resolve()` is the *only*
public entry point, and `_resolve_side()` always calls `.resolve()` on
both sides for all three operations, `UNION` included — there is no
`query()`-only path anywhere in the class today.

`INTERSECT`/`SUBTRACT` genuinely need resolved data for their join key
(already established), so a query()-only mode only makes sense for
`UNION` specifically — `UNION`'s own dedup only needs `ReferenceResult3`'s
full `__eq__` (`path`+`uuid`+`data`+`identity`), which works fine whether
`data`/`identity` are populated or not (comparing `None`s is safe). Worth
deciding whether a cheap, query()-only `UNION` mode is actually wanted
(matching 4.2's own stated intent) before building it — not yet designed
beyond "it would only apply to `UNION`."

## `ReferenceExpression3` `paths`-vs-`values` compatibility matrix — not built

Settled 2026-08-23 (see `references_v3_expressions.md`'s own "`paths` vs.
`values` sides" section for the full matrix) while working through what
should happen when one side of a `UNION`/`SUBTRACT`/`INTERSECT` has no
trailing `VALUE`-role accessor (`paths` -- plain path+uuid) and the other
does (`values` -- a real scalar in `.data`). Live-traced the current code
first (`reference_expression_3.py`'s `_intersect`/`_subtract`/`_keys`) to
find the actual behavior, not just what the semantics notes claimed:
today, `None`-valued `.data` (which is what every item on a `paths` side
has) is silently treated as "never matches" — meaning `INTERSECT` with a
`paths` side quietly comes back empty, and `SUBTRACT` quietly comes back
as an unfiltered copy of the left side, in every case, with no error. This
is a real, currently-shipped gap, not just an untested edge case — nothing
raises where the settled design now says it should.

**None of this is built yet.** Needed:
- **A `paths`/`values` classifier** for a side (plain reference string or
  sub-`ReferenceExpression3`) — static, from the parsed reference's own
  trailing function, not from resolved data (a per-item legitimate `None`,
  e.g. an optional field absent for one entity, must stay distinct from
  "this reference structurally has no accessor at all").
- **`UNION` validation**: raise if the two sides' kinds differ.
- **`SUBTRACT`/`INTERSECT` rewrite**: `values`/`values` stays as today
  (compare by `.data`); `paths`/`paths` and `values`(LHS)/`paths`(RHS) need
  a *new* identity-based comparison (`path`+`uuid` together, not today's
  `.data`-only comparison) — this doesn't exist in the code at all yet;
  `paths`(LHS)/`values`(RHS) raises unless RHS is UUID-valued, in which
  case compare LHS's *native* `uuid` (no accessor involved) against RHS's
  `.data`.
- **A declarative "this accessor produces a UUID" marker on `Function3`**
  (e.g. `:uuid()`, `:run_uuid()`) — checked generically by
  `ReferenceExpression3`, not hardcoded by function name. Same principle
  as the `_check_position()`/`POSITIONS` precedent already used elsewhere
  in this codebase (see the `resolve_kind` hardcoded-dispatch entry above)
  — don't invent a second, parallel hardcoded-name mechanism right next to
  the one already flagged as debt.

## Retire `:path()`; move Rule 1 enforcement from `query()` to `resolve()`

David, 2026-08-22, deciding while reviewing the compendium's "Rule 2/Rule 3"
notes (path/field accessors exempt from Rule 1, always poolable): **getting
paths is not the same as accessing files.** A field/file accessor trying to
read *content* for more than one matched entity is illegal, no argument —
but a `query()` that merely points to multiple entities is fine in
principle. `:path()` exists today only to route around Rule 1's query()-time
restriction (wrap a whole-resource content function, return its path
instead of content, since a path is cheap/poolable) — but that whole
function becomes redundant if the restriction itself simply moves to
`resolve()` instead of being enforced inside `query()`. David's decision:
**`query()` should always be allowed to return multiple matches, regardless
of which accessor function is present; only `resolve()` (actually reading
content) raises when asked to resolve more than one match at once.**
`:path()` is retired — the same job is done by just calling `query()` on
the ordinary accessor and not resolving it.

This actually realigns the code with what Rule 1's own docstring already
said: "resolving full manifest content always touches exactly one entity"
— resolve-scoped language, even though the current enforcement
(`if has_manifest and len(candidates) > 1: raise ...`) lives inside
`query()` itself, in all three finders.

**Likely a bigger simplification than just deleting `:path()`, not just a
retirement** — a lot of the currently-tracked `'*'`-traversal guards (both
the FILES-untouched entry and the RESULTS/CSVPATHS partial generalization)
reject combining `'*'` traversal with `:manifest()`/`:path()`/a field-
accessor specifically *because* of this same query()-time ambiguity. Once
that restriction no longer applies at query() time, several of those
guards may turn out to be unnecessary rather than needing to be built out
— re-audit case by case once this lands, rather than assuming it dissolves
everything at once.

**Explicitly a deliberate breaking change, not an oversight** (David: "now
is the time to break things... it is never too soon to make a better
decision") — the current query()-time raise has real tests locking it in
(`TestManifestCombinedWithNameThree` and siblings, across all three
finders' test files). Those need rewriting to assert the new query()-
succeeds/resolve()-raises split, not just deleted.

Work: remove `Path3`/`path_3.py` and its factory registration; move the
single-entity check out of each finder's `query()` and into `resolve()`/
`_extract_data()` (all three finders — `files_reference_finder_3.py`,
`csvpaths_reference_finder_3.py`, `results_reference_finder_3.py`); rewrite
the tests that currently assert query()-time raising; re-audit the `'*'`-
traversal guards afterward to see which are still actually needed.

## `resolve_kind`'s hardcoded name-tuple dispatch — needs examination for clarity/impact before deciding

Found 2026-08-22 while checking whether the compendium's old §6 ("Known
gaps") still had anything current in it. `Reference3.resolve_kind` (`reference_3.py`)
dispatches `METADATA_FILE`/`METADATA_FIELD` classification off two hardcoded
name-string tuples, `_METADATA_FILE_FUNCTIONS`/`_METADATA_FIELD_FUNCTIONS`
(38 names total) — confirmed every single name in both tuples *is* backed
by a real, registered `Function3` today (checked all 38 directly against
the function registry, none missing). So nothing is factually broken.

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
clarity, not yet a committed-to fix.

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

## Predicate-argument field accessors (`:on_arrival(:not_none())`) — not built anywhere

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

Still to design/build:
- `Idchain3.ARG_TYPES` needs to accept a predicate function (`:not_none()`
  and friends) alongside its current `(str, Regex3)` — confirmed
  `ARG_REQUIRED = True` today, so a bare, argument-less `:idchain()` stays
  illegal; `:not_none()` is the sanctioned way to say "any idchain at all,"
  not an empty-argument special case.
- `:not_none()` itself is still not a registered function anywhere
  (unchanged from above).
- The actual GATE dispatch mechanism — a chained sibling function whose
  own predicate argument controls whether the *preceding* function's
  result is emitted at all — is additive to `:idchain()`'s existing filter
  behavior, not a replacement for it, and still needs building from
  scratch; nothing dispatches this today.

## Corrections needed in the new `:manifest()`/`:definition()` compendium section (David's draft, 2026-08-21)

While reviewing David's own replacement text for the "root `:manifest()`
and `:definition()` files" section (aimed at cutting implementation-history
cruft down to design intent, which the old section had a lot of):

- `$acme.files.:manifest():last()` was given as an example returning "the
  last file registration data captured in the **global** files ledger
  manifest" — wrong on two counts. A literal root_major (`acme`) can never
  mean the global ledger — only `$*` reaches that; `$acme` always means
  acme's own manifest.json. And even read as "acme's own manifest, last
  entry" (not the global one), that exact shape is the unbuilt gap in the
  bucket-list entry directly above this one — it raises today, it doesn't
  work. Needs splitting into two correct examples: `$*.files.:manifest()
  :last()` (global ledger's last entry — genuinely works today) and
  `$acme.files.:manifest():last()` (acme's own manifest's last entry — does
  not work yet).
- The draft called the definition-file function `:description()`; the real,
  existing function is `:definition()`. David confirmed this was just a
  slip while drafting, not an intentional rename.

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
— there is no equivalent call for a literal root_major.

Open question David flagged, not yet settled: is this actually a good/
wanted alternative to a full `:name(...)` + name_three reference (which
already gets you "the matched version's own manifest entry," a different,
narrower thing), or just a symmetry nicety worth having anyway? Worth
resolving before building, not just building because Rule 1b's shape
suggests it.

## Split `:home()`'s field-read job into scope-specific functions; `:home()` itself stays, for the zero-level placeholder role only

David, 2026-08-21, refined 2026-08-24: no manifest anywhere has a literal
`"home"` key — confirmed, `Home3.KEY` (`home_3.py`) reads `file_home`
(FILES), `named_paths_home` (CSVPATHS), `run_home` (RESULTS run scope),
`instance_home` (RESULTS instance scope), never a bare `"home"`.

**`:home()` today does two jobs, and only one of them is being retired.**
- **The field-read job (going away)** — reading whichever of the four real
  keys above off whatever entity a pointer already selected. Replaced by
  four separate, obviously-named functions matching the real keys:
  `:file_home()`, `:group_home()`, `:run_home()`, `:instance_home()`. (An
  earlier version of this note also considered a fifth name, `:name_home()`
  — dropped, 2026-08-24: there is no fifth job needing a name, only these
  four real keys exist.)
- **The zero-level placeholder job (staying, under the same name)** —
  David, 2026-08-24, explicit: "`:home()` as the means of accessing the
  0-level template files and results has to remain. That `:home()` we
  don't have a replacement for — and I can't think of a better name for
  the function." FILES and RESULTS only (CSVPATHS has no path dimension,
  so no zero-level concept to place-hold for). This is the *only* legal
  way to express "nothing narrows here" at a bare, zero-segment position —
  a truly empty `name_one` isn't legal grammar at all (`path_prefix`
  requires >= 1 segment).

So this is no longer a full retirement, just a narrowing of `:home()`'s
scope to exactly one job. Live-confirmed 2026-08-24 exactly what that
remaining job still does and doesn't do today, using
`$acme.results.:last()` / `:home():last()` / `:flatten():last()` as the
test case (fixture: one zero-level run 2026-01-01, one 1-level-templated
run 2026-01-05, later):
- `$acme.results.:last()` and `$acme.results.:home():last()` give the
  **identical** result (the zero-level run only, templated run excluded
  even though it's chronologically later) — `:home()` combined with a
  real pointer is fully redundant with the bare pointer alone today, since
  a bare pointer is *already* zero-level-scoped (settled 2026-08-10). The
  placeholder role only does something distinct when `:home()` is used
  *alone*, no pointer present (`$acme.results.:home()` -> every zero-level
  run, unreduced — the one thing nothing else can express).
- `$acme.results.:flatten():last()` gives the templated run instead
  (2026-01-05) — the true any-depth latest, correctly different from both
  of the above.

**`:home()` vs. `:all()`, precisely (David, 2026-08-21, still applies)**:
not just a different depth — a different axis entirely. `:home()`'s
placeholder role indicates the zero-level ("no template") homes as a
**complete path** — nothing narrows further, so the result already *is*
the whole entity's own home directory. `:all()` indicates **any value of
one path segment** — a path *part*, the observed value at exactly one
wildcarded position — with the complete path only emerging once that
grouping resolves (and reduces, if a pointer is present).

Work: build the four new field-read functions (`:file_home()`,
`:group_home()`, `:run_home()`, `:instance_home()`); narrow `Home3`
(`home_3.py`) itself down to only the zero-level placeholder role
(`SOURCE`/`KEY`-driven field read goes away, the bare-zero-level query()
branches in `files_reference_finder_3.py`/`results_reference_finder_3.py`
stay); fix the compendium's own now-incorrect claim about `:home()`
"reverting to its ordinary job of reading the field" once a pointer joins
the chain — per the live test above, it doesn't revert to reading
anything, it's simply redundant/inert once a pointer is present, since
the pointer's own zero-level scoping already does the same narrowing.

## `#name_two` (XLSX worksheet marker) — not built anywhere

David, 2026-08-21: raised while reviewing the compendium — does
`ReferenceResult3` need a field for which worksheet was found? Confirmed
it does not have one today, and neither does anything else exist yet to
make that field meaningful. **Resolved, 2026-08-21: reuse `identity`**
(David: "identity works quite well with worksheet (name_two)") rather
than adding a dedicated field — no `ReferenceResult3` change needed when
this actually gets built, just populate `identity` with the worksheet
name the same way CSVPATHS already populates it with a statement
identifier.

- The grammar already has the slot (`name_one: path_prefix ("#" name_two)?
  func_chain?`, `reference_grammar_3.py:102,109`), and it parses fine
  (`NameOne3.name_two`, `ReferenceParser3.name_two`) — but **every** finder
  rejects it outright the moment it's present, including `FilesReference
  Finder3` itself (`files_reference_finder_3.py:134-138`), where it's
  documented as the eventual, files-only, XLSX-worksheet meaning.
  CSVPATHS/RESULTS correctly reject it as files-only; FILES rejecting it
  too just means the feature isn't built yet anywhere.
- Work still needed: teach `FilesReferenceFinder3` to accept `#name_two`
  and actually read the named worksheet, then populate the resulting
  `ReferenceResult3.identity` with it.

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
  pattern()` only accepts `:name("...")` as a function-valued segment, and
  `Name3.ARG_TYPES = (str,)` (no `Regex3` support).
- `@variable` (`Variable3`) is parsed but not usable anywhere as a real
  argument — no currently-registered function's `ARG_TYPES` includes it.
  The only place it's structurally accepted at all is a bare `@variable`
  inside `{...}` string interpolation, and even there it can't be
  *evaluated* yet (see interpolation-evaluation item below).
- Found 2026-08-24 (Phase 1 compendium review, item 3.12): there is no
  registration mechanism at all yet, either — no finder has any "give me a
  value for `@name`" API (confirmed via grep, nothing like `set_variable`
  exists anywhere in `csvpath/references/`). **David, 2026-08-24: this is
  a required, must-have capability for RC, not optional or deferrable** —
  the compendium's own 3.12 originally said "an implementation detail,"
  which was meant only to mean "no strong opinion on the mechanism/
  user-level interface," not "low priority." Compendium text corrected to
  say so explicitly. Both pieces are needed before RC: the registration
  API itself, and `@variable` actually being usable as a real function
  argument (see the entry directly above this one) plus evaluated at
  resolve time (see the `{...}` interpolation-evaluation item under
  "Bigger, standing items," which shares the same variable-resolution
  prerequisite).

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

## `'*'` traversal — FILES, essentially untouched by the recent RESULTS/CSVPATHS work

- `FilesReferenceFinder3`'s own `_query_star_traversal()` still rejects
  combining `'*'` traversal with `:manifest()`/`:definition()`/`:path()`/a
  field-accessor function outright — the same class of gap RESULTS/CSVPATHS
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
