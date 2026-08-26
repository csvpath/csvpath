# References v3 — Completed Work (formerly on the bucket list)

Companion to `deferred_work_bucket_list.md`. Every entry here started life
on that list and was later built/fixed/resolved — moved here on 2026-08-26
so the bucket list only shows what's actually still outstanding. Kept
verbatim (including its own history/backstory) rather than trimmed to a
one-line changelog, since the reasoning behind *why* something was built
the way it was is often exactly what the next person touching it needs.

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
