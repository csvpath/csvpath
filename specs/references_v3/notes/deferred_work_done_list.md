# References v3 — Completed Work (formerly on the bucket list)

Companion to `deferred_work_bucket_list.md`. Every entry here started life
on that list and was later built/fixed/resolved — moved here on 2026-08-26
so the bucket list only shows what's actually still outstanding. Kept
verbatim (including its own history/backstory) rather than trimmed to a
one-line changelog, since the reasoning behind *why* something was built
the way it was is often exactly what the next person touching it needs.

---

## `ReferenceExpression3` UNION compatibility rule revised to LHS-driven accessor-equality — BUILT 2026-08-26

Same day as the `paths`-vs-`values` matrix entry below, but a genuine
revision of it, not a duplicate — David reopened `UNION`'s own compatibility
check almost immediately after that build landed, via a design note about
"`UNION` of paths": bare-path `query()`-level unions (no field accessor on
either side) need to work without regard to uuid or any resolved data, and
the boundary condition ("LHS resolves to a value that does not match the
type of RHS's value -> raise") needed a real mechanism, not just prose.

Worked through in conversation, not assumed:
- First clarified whether the rule was meant to be symmetric or driven by
  one side — David: **genuinely LHS-driven**, not symmetric (confirmed
  directly, not inferred).
- Then how "does not match the type" should actually be checked -- runtime
  value-type comparison (`isinstance`/`type()` on resolved `.data`) vs.
  something declarative. David's own proposal, verbatim: *"could we not do
  it by comparing functions? a `:uuid() == :uuid()`, `:type()` may or may
  not equal `:type()`, `:type("csv") != :type("xlsx")`. So the accessor
  must equal. If it does, we then ask are the values equal?"* -- i.e.
  compare each side's own terminal `FunctionCall3` (function name +
  argument together) for structural equality, not the resolved values'
  runtime types. Confirmed `FunctionCall3.__eq__` (`reference_3.py`)
  already does exactly this comparison (`name` + `arg`), so no new
  comparison primitive was needed, only wiring it into `UNION`'s own
  check.
- This deliberately **replaces** the earlier `PRODUCES_UUID`-based "both
  sides produce a uuid" framing from the original design note, rather than
  layering a separate uuid-specific tier on top of it: `:uuid()` and
  `:run_uuid()` both produce a uuid but are not the *same* accessor, so
  under the final rule they are NOT union-compatible, even though they
  would be directly comparable under `SUBTRACT`/`INTERSECT`'s own
  uuid-valued-RHS case (a genuinely different, still-unchanged rule --
  see the matrix entry below). `:uuid() == :uuid()` and a bare `:type()`
  against another bare `:type()` are both still fine (identical accessor);
  `:type("csv")` vs. `:type("xlsx")` is not (same function, different
  argument).

**Built**: `ReferenceExpression3._terminal_value_call()` (new, returns the
side's own terminal `ROLE == VALUE` `FunctionCall3`, or `None` for a
`paths` side -- `_kind()` rewritten as a one-line consumer of it) and
`_check_union_compatible()` (new, replaces the inline symmetric check
`resolve()` used to run for `UNION` -- if LHS is `paths`, returns
immediately (RHS unions freely, by path); otherwise raises unless RHS's
own terminal `FunctionCall3` equals LHS's, via the existing `__eq__`).
`resolve()`'s `UNION` branch is now just `self._check_union_compatible();
return self._union(...)`.

**Also resolves the separate, previously-open "`ReferenceExpression3` has
no `query()`-only mode" bucket-list item** (found 2026-08-24, compendium
4.2) -- decided, in the course of this same conversation, NOT to build a
distinct `query()`-only code path. The compatibility check itself was
already purely structural (parsed accessors, never resolved data) before
this revision and stays that way; `resolve()` remains the sole public
entry point and still fully resolves both sides regardless of kind --
there was never a real cost to resolving that a `query()`-only shortcut
would have avoided, once the check moved to comparing parsed accessors
rather than resolved values.

Tests: rewrote `TestPathsVsValuesEndToEnd.test_union_of_a_paths_side_and_a_values_side_raises`
(`tests/references/test_reference_expression_3.py`) into three tests
reflecting the new asymmetric rule --
`test_union_of_a_paths_left_and_values_right_succeeds_by_path` (no longer
raises -- LHS `paths` unions freely),
`test_union_of_a_values_left_and_paths_right_raises` (new -- the reverse
order now matters), and
`test_union_of_two_values_sides_with_different_accessors_raises` (new --
`:named_paths_name()` vs. `:run_uuid()`, both `values` but not the same
accessor). Updated `references_v3_expressions.md`'s own matrix and
"Why SUBTRACT/INTERSECT's raise is asymmetric" section to describe the
new rule instead of the superseded symmetric one.

---

## `ReferenceExpression3` `paths`-vs-`values` compatibility matrix — BUILT 2026-08-26

Settled 2026-08-23 (see `references_v3_expressions.md`'s own "`paths` vs.
`values` sides" section for the full matrix) while working through what
should happen when one side of a `UNION`/`SUBTRACT`/`INTERSECT` has no
trailing `VALUE`-role accessor (`paths` -- plain path+uuid) and the other
does (`values` -- a real scalar in `.data`). Live-traced the current code
first (`reference_expression_3.py`'s `_intersect`/`_subtract`/`_keys`) to
find the actual behavior, not just what the semantics notes claimed:
`None`-valued `.data` (what every `paths`-side item had) was silently
treated as "never matches" — `INTERSECT` with a `paths` side quietly came
back empty, `SUBTRACT` quietly came back as an unfiltered copy of the
left side, in every case, with no error. A real, currently-shipped gap,
not just an untested edge case.

**Continued straight through the bucket list, per David's own "step
through in order unless you spot a better one" instruction, then flagged
a real ordering issue**: the item ahead of this one (`ReferenceExpression3`
query()-only mode) explicitly needed a yes/no decision before any code
made sense ("worth deciding whether... actually wanted... not yet
designed"), while this one had an already-settled design and a confirmed
live bug. David: skip ahead to this one now, circle back to the decision
-needed one after.

**Built, all four pieces the bucket-list entry named**:
- **The `paths`/`values` classifier** (`ReferenceExpression3._kind()`) —
  static, from the parsed reference's own `terminal_functions` (see
  below), checking each function's own `ROLE` directly against the
  registry (`ReferenceFunctionFactory`) rather than via `Reference3.
  resolve_kind`'s hardcoded name tuples — deliberately avoiding a second
  consumer of that already-flagged debt (see the `resolve_kind` bucket-
  list entry, still open). A side is `VALUES` if its terminal chain
  includes any `ROLE == Function3.VALUE` function, `PATHS` otherwise.
- **`Reference3.terminal_functions`** (`reference_3.py`) — extracted as a
  new public property from what used to be `resolve_kind`'s own inline
  computation (pure refactor, `resolve_kind` itself unchanged/untouched
  behavior, still hardcoded-tuple-based) — needed so the classifier
  above computes the same terminal chain without duplicating the
  traversal logic.
- **`UNION` validation** — raises if the two sides' kinds differ
  ("concatenating two structurally different result shapes into one bag
  is never meaningful, regardless of order"). **Superseded later the same
  day** — see the entry above this one ("`ReferenceExpression3` UNION
  compatibility rule revised to LHS-driven accessor-equality"), which
  replaces this symmetric kind-check with David's own "compare the
  accessors, not the value types" rule. `_kind()` itself, and everything
  else in this entry (the classifier, `terminal_functions`, the
  `SUBTRACT`/`INTERSECT` rewrite, `PRODUCES_UUID`), is unaffected — only
  `UNION`'s own check changed.
- **`SUBTRACT`/`INTERSECT` rewrite** — `values`/`values` unchanged
  (compare by `.data`, the existing `_intersect`/`_subtract` methods,
  untouched); two new comparison methods for the other three matrix
  rows: `_filter_by_identity()` (`paths`/`paths`, or `values`(LHS)/
  `paths`(RHS) — compares `(path, uuid)` tuples, LHS's own `.data` if any
  survives unchanged in the output) and `_filter_by_native_uuid()`
  (`paths`(LHS)/`values`(RHS) where RHS is uuid-valued — LHS's own
  native `.uuid` compared directly against RHS's `.data`). `resolve()`
  itself now branches on `right_kind` first (covers both identity-basis
  rows in one check), then `left_kind` if right is `values` (raises, or
  falls back to native-uuid comparison, per the matrix).
- **`Function3.PRODUCES_UUID`** (new declarative class attribute,
  default `False`) — checked generically by `ReferenceExpression3`, not
  hardcoded by function name, same `POSITIONS`/`_check_position()`
  precedent already established elsewhere. Set `True` on the four
  functions that genuinely produce a uuid: `:uuid()`, `:run_uuid()`,
  `:named_file_uuid()`, `:named_paths_uuid()` — confirmed by reading each
  one's own `KEY`, not assumed from the name alone.

Tests: `TestFilterByIdentity`/`TestFilterByNativeUuid` (synthetic-
`ReferenceResults3` unit tests, mirroring the existing `TestIntersect`/
`TestSubtract` style) plus `TestPathsVsValuesEndToEnd` (5 real, end-to-
end tests through `resolve()` and the existing `orders_archive` fixture
— UNION-mismatch-raises, `paths`/`paths`, `values`(LHS)/`paths`(RHS)
keeping LHS's own `.data`, `paths`(LHS)/`values`(RHS) non-uuid-valued
raising, and the uuid-valued case actually matching) in
`test_reference_expression_3.py`; `TestTerminalFunctions` in
`test_reference_3.py`; widened `PRODUCES_UUID` assertions in all four
uuid functions' own unit tests. `tests/references/` now 1423 passed, up
from 1408.

---

## `Function3.describe()`'s markdown-rendering companion — BUILT 2026-08-26

Compendium 5.4: "Reference functions are self-documenting... must be
able to output .md in a similar way to `csvpath/cli/function_describer.py`."
`Function3.describe()` already existed but only returned a plain dict
(`name`/`summary`/`role`/`datatypes`) meant for a future type-ahead
layer, not human-readable output — the actual rendering layer 5.4
requires didn't exist.

**Built as a new, separate class** (`Function3Describer`, `csvpath/
references/function_describer_3.py`), not a reuse of the match-language
`FunctionDescriber` and not a change to `Function3.describe()` itself
(left alone — still the machine-readable half, unchanged contract).
Match-language functions have argsets/overloads/qualifiers that
references-v3 functions simply do not (at most one arg, no overloads at
all), so a from-scratch, much simpler renderer fit the actual `Function3`
model better than adapting the heavier match-side one. Two entry
points: `describe(function_cls)` (one function's own markdown block —
name, summary, role, datatypes, argument type/required-ness, `POSITIONS`
per datatype, and — for field accessors — `SOURCE`/`KEY`/`LEDGER_KEY`/
`BARE_SOURCE` when declared) and `describe_all()` (the whole registry as
one combined document: an alphabetical index linking down to each
function's own block, mirroring `FunctionDescriber.describe()`'s own
"[[Back to index]]" convention, just inverted — one document, not one
page per function).

New `ReferenceFunctionFactory.registered_names()` (`reference_function_
factory_3.py`) — `describe_all()` needed to enumerate every registered
name without reaching into the factory's own "private" `_FUNCTIONS` dict
from outside the class.

**Deliberately just a markdown-STRING producer** — writing the result to
a file, or wiring it into any interactive CLI (the way `FunctionLister`
wires the match-language version into a REPL picker), is a separate
integration question, out of scope here (v3 is not wired into
production yet, see this list's own "Bigger, standing items"). Also
deliberately side-stepped GitHub-flavored-markdown's own heading-to-
anchor slugify ambiguity (different renderers handle punctuation in
headings differently) by keeping each function's own heading a plain
`## {name}` with no backticks/colon/parens, so the index's own `#{name}`
links resolve predictably everywhere rather than replicating one
specific renderer's exact algorithm.

Tests: `tests/references/test_function_describer_3.py` — one function's
own block (name/summary/role/datatypes/argument-required-ness/source-
key/bare-source/positions, spot-checked against `Year3`/`Idchain3`/
`Template3`), plus `describe_all()` (every registered name appears in
the index exactly once, one full block per function, no duplicates).
`tests/references/` now 1408 passed, up from 1397.

---

## Predicate support functions (5.31), plus the `:idchain()` filter half of predicate-argument accessors — BUILT 2026-08-26

Found 2026-08-24 (Phase 1 compendium review). The compendium lists eight
predicate-support functions: `:true()`, `:false()`, `:none()`,
`:not_none()`, `:empty()`, `:not_empty()`, `:regex(/.../)`, `:having(...)`.
Only `:having()` existed. `:regex()` as a *function* (distinct from
`Regex3`, the `/pattern/` literal type) stays tracked separately under
the grammar/argument-type-gaps entry, not double-counted here.

**Same entanglement risk as the date/time functions (previous entries)
— the six leaf functions would be inert without a real consumer.**
Continuing straight through the bucket list in order (David's own
call — "step through the items unless you spot a better ordering"),
but the natural, already-*settled* consumer wasn't a later list item at
all — it was sitting right there in the still-open "Predicate-argument
field accessors" entry: compendium 5.36/§4.13/4.14 had already agreed
`:idchain()` should accept a predicate argument (`:errors(:idchain(
:not_none()))` — "any idchain at all", a filter), with `Idchain3.
ARG_TYPES` widening explicitly named as the one remaining, ready-to-
build piece. Wired that in the same pass, rather than leaving the six
functions with zero consumers the way a stricter "one bucket item at a
time" reading would have.

**Built**: `:true()`/`:false()`/`:none()`/`:not_none()`/`:empty()`/
`:not_empty()`, all `ROLE = VALUE`, `DATATYPES = (FILES, CSVPATHS,
RESULTS)` (datatype-agnostic, matching how they are meant to nest
inside any field accessor's argument regardless of datatype, even
though the one consumer wired up so far is RESULTS-only). New shared
base class, `PredicateFunction3` (`csvpath/references/functions/
filters/predicate_function_3.py`), each declaring `matches(value) ->
bool` — added specifically so a consumer (e.g. `Idchain3`) can declare
`ARG_TYPES` generically as `(..., PredicateFunction3)` instead of
enumerating all six concrete classes by name, matching the project's
own declarative-over-hardcoded-list preference (see the `resolve_kind`
bucket-list entry) — a future predicate function automatically works
with any existing consumer with no changes there at all.

`Idchain3.ARG_TYPES` widened to `(str, Regex3, PredicateFunction3)`;
`Idchain3.matches()` now delegates to the nested predicate's own
`matches()` when `self._arg` is one, checked before the existing str/
Regex3 branches. No special-casing needed for how a predicate function
actually gets built as `:idchain()`'s own arg — `ReferenceFunctionFactory.
build()` already recursively builds a nested `FunctionCall3` arg into a
real `Function3` instance (the same generic mechanism `:from(:index(2))`
already relies on), confirmed live before assuming it would "just work".

**Still explicitly NOT built** (separately tracked, see the bucket
list's own "Predicate-argument field accessors" entry): the GENERIC
"any field accessor accepts a predicate argument" mechanism (the FILES
`:on_arrival(:not_none())` example that originally motivated the whole
predicate-argument idea) — `Idchain3` accepting one is a narrow, specific
fix for one function, not a generic dispatch mechanism any OTHER field
accessor gets for free; and the GATE half (a chained sibling function,
e.g. hypothetical `:errors():idchain(:not_none())`) — additive to the
filter behavior, nothing dispatches it yet.

Tests: `tests/references/functions/filters/test_{true,false,none,
not_none,empty,not_empty}_3.py` (one file each, metadata + `check_valid()`
+ `matches()` truth-table), `test_predicate_function_3.py` (base class
raises `NotImplementedError` if a subclass forgets to override
`matches()`), widened `test_idchain_3.py` (new `ARG_TYPES` assertion
plus a `matches()` delegation test), and one live end-to-end test
through a real `ResultsReferenceFinder3`
(`test_errors_with_idchain_not_none_filters_to_entries_that_have_any_source`,
matching compendium 5.36's own worked example exactly — some errors
have a `"source"` field, one does not, `:not_none()` filters to just
the ones that do). `tests/references/` now 1397 passed, up from 1370.

---

## `@variable` registration and `{...}` interpolation evaluation, both halves — BUILT 2026-08-26

Compendium 3.12: "Prior to query, a reference finder can be given
variables that may be used in references. A variable can be any Python
object, but the variable value will be put into a string context so its
`__str__` must make sense... Variable support, including registration, is
a required, must-have capability for RC." Built immediately after the
date/time functions (previous entry) and their path-segment/interpolation
consumption paths — David's own call: "knock out variables now... we have
one use case, interpolation, right at hand," reusing `_resolve_value()`
(the evaluator just built for the function-call half of interpolation) for
the other half it always had a placeholder branch for.

**The key design question, resolved by reading 3.12 literally rather
than assuming**: this is NOT about reaching into a live `CsvPath`
instance's own runtime `variables` dict (`csvpath.py`'s `set_variable()`/
`get_variable()`) — those are scoped to one specific, currently-running
statement, which does not exist at all when a reference is resolved
standalone (v3 is not wired into production yet, see the bucket list's
own "Bigger, standing items"). 3.12's own wording — "a reference finder
can be given variables" — describes something much simpler: explicit,
finder-level registration, done by whoever constructs/uses the finder,
before resolving.

**Built**: `ReferenceFinder3.__init__` gained an optional `variables:
dict | None = None` kwarg (stored as `self._variables`), plus two
post-construction registration methods — `set_variable(name, *,
value)` (mirrors `CsvPath.set_variable()`'s own keyword-only `value`
convention) and `set_variables(dict)` (bulk merge). `_compile_path_
pattern()`/`_resolve_value()` were converted from `@staticmethod` to
ordinary instance methods (every call site already used `self.`-style
calls, so no call site needed to change) so `_resolve_value()` could
reach `self._variables` — its own `Variable3`-part branch, which used
to always raise, now looks the name up and raises only if nothing was
registered for it.

Scoped deliberately narrow, matching David's own framing ("one use
case, interpolation, right at hand"): `@variable` is now usable inside
`{...}` interpolation only. Whether `@variable` should ALSO be usable
as some other function's own direct argument (e.g. a hypothetical
`:uuid(@myvar)`, tied to the separate dual-selector/value-accessor
design item) is untouched, independent follow-up work, not needed to
close this out.

Tests: 6 new cases in `test_reference_finder_3.py`'s `TestResolveValue`
(registered-variable substitution, non-string variable values via
`__str__`, unregistered-variable raises, both registration APIs) plus
one live end-to-end test through a real `FilesReferenceFinder3`
combining a variable AND a clock function in one interpolated string
(`:name("partner-{:year()}-{@company}")`, matching the compendium's
own 5.37 worked example exactly). `tests/references/` now 1370 passed,
up from 1364. Full local-backend suite reconfirmed at the known
11-failure (SFTP/S3/Nos, unrelated) baseline afterward.

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
