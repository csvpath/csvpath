
# REFERENCE EXPRESSIONS

A reference expression is a logical operation(s) on references. The goal is to answer questions that a single reference is insufficient to answer on its own. For example:

    *"find all the named-files that were used in runs where the named-paths group was updated yesterday."*

We can find all the named-files used in runs from the RESULTS datatype. And we can find all the named-paths group updated yesterday from the CSVPATHS datatype. But we need a set operation-like evolution applied to both to answer the full question. The set operation and its references is a reference expression.

The result of a reference expression is ReferenceResults, same as the result of a single reference.


## OPERATIONS

A reference expression has one operation which is one of:
- UNION
- SUBTRACT
- INTERSECT

UNION bags the two ReferenceResults sets together. SUBTRACT removes the right-hand side from the left-hand side (as in "ref subtract ref"). And INTERSECT returns bag of the ReferenceResults items found on both sides.

At this time we don't contemplate ordering results, though SUBTRACT will retain the order of the left-hand side.


## SUB-REFERENCE EXPRESSIONS

A reference expression may have another reference expression on either side. Each side is reduced to a ReferenceResult before the set operation is applied.


## EXAMPLES

The pseudocode below is for directional illustration only. It is not settled in form.

#
# find the named-paths groups versions that caused errors yesterday
#
exp = ReferenceExpression.intersect()
#
# register some variables in this case the variable is @ids
#
exp.set("identities", ids = ["my_validations", "new_validations"])
#
# fails is on left, changes on right
#
fails = exp.results_refrence("$*.csvpaths.:flatten():from(:yesterday()).:identity(@identities)):has_errors():named_paths_uuid()")
changes = exp.csvpaths_reference("$*.csvpaths.:all():having(:identity(@identities))")
#
# get the reference results of executing the expression
#
exp.query()

---

## Questions

Q: give me all the runs where the named-paths group included a csvpath with the identity "orders"

A: INTERSECT: in results return :named_paths_group() == in csvpaths return :having(:identity(id)) return :named_paths_name()

This uses INTERSECT in order to return the runs, not the instances within the runs. If we wanted to just get the instances we could simply use :having(id) on results. (I realize we'd need to add that function to results, but that is something we should do).

---

## Semantics notes

- The join/comparison key for INTERSECT/SUBTRACT is whatever scalar a side's
  own trailing field accessor resolves to (`:identity()`, `:named_paths_name()`,
  `:uuid()`, `:time()`, etc). A key that resolves to a list/dict
  (`:named_paths_identities()`, `:file_fingerprints()`,
  `:scripts()`/`:webhooks()`/`:transfers()`) is never usable as a join key
  and must raise clearly rather than fail deep inside a set/dict. See
  "`paths` vs. `values` sides" below for when a side with *no* trailing
  accessor (a plain path+uuid result) is or isn't usable.
- `None`-valued keys never match anything, on either side -- excluded from
  membership testing entirely, never treated as equal to each other.
- UNION does not correlate the two sides at all -- pure concatenation of
  each side's own native results, deduplicated by full `ReferenceResult3`
  equality (`path`+`uuid`+`data`+`identity`). It never uses the join key,
  never filters, never multiplies rows. Seeing which items on one side pair
  with which on the other is done after the union, by the caller, comparing
  `.data` across the merged results -- not a separate operation.
- INTERSECT/SUBTRACT are filters, not joins that multiply rows -- a left-hand
  item survives (INTERSECT) or is removed (SUBTRACT) based on whether its key
  exists anywhere on the right, regardless of how many right-hand items share
  that key. **Only the right side is reduced to a plain set of keys** --
  which right-hand item carried a given key never matters, right-hand items
  never appear in the output. **The left side is never collapsed by key** --
  only deduplicated by full `ReferenceResult3` equality (drops true duplicate
  items, never a different item that merely shares a key), then each
  surviving left item is filtered individually against the right side's key
  set. (Two groups sharing an identity, with 2 and 3 runs respectively, must
  produce 5 results from INTERSECT, not 1 per group -- collapsing the left
  side by key first would be wrong.) A caller who wants "one result per
  distinct key" gets that by calling `ReferenceResults3.deduplicated()`
  themselves on whichever side needs it before handing it to an expression --
  INTERSECT/SUBTRACT never force that.
- Worked example (two named-paths groups sharing the identity "orders", 5
  runs total: 2 for one group, 3 for the other):
    - both groups' current versions have "orders": UNION gives 7 results
      (5 runs + 2 groups).
    - one group is deleted: 6 results (5 runs still exist -- run history
      doesn't disappear with the group -- + 1 surviving group).
    - neither group's *current* version has "orders" anymore: 5 results
      (all 5 runs, 0 groups) -- every run orphaned.
    - INTERSECT for the same three scenarios: 5, 2, 0.

### `paths` vs. `values` sides

A side is **`paths`** if its reference has no trailing `VALUE`-role
accessor (a plain path+uuid result -- `.data` is `None`), or **`values`**
if it does (a real scalar in `.data`). Every result, regardless of kind,
always has its own real `path`/`uuid` from `query()` -- `values` doesn't
mean "no path," it means "also has a value."

Settled compatibility matrix (David, 2026-08-23):

| Operation | LHS \\ RHS | Result |
|---|---|---|
| UNION | LHS is `paths` | normal -- RHS unions freely, by path alone, regardless of RHS's own kind |
| UNION | LHS is `values`, RHS's terminal accessor shares the LHS's own conceptual `KIND` (e.g. both `"uuid"`, both `"name"`), or is the literally identical accessor when neither declares a `KIND` | normal -- dedup by full `ReferenceResult3` equality |
| UNION | LHS is `values`, RHS's terminal accessor shares neither a `KIND` nor literal identity with the LHS's own (or RHS is `paths`) | **raise** -- e.g. `:type()` vs. `:status()` (both happen to resolve to a string, but a file extension and a status message are not the same kind of thing, and neither declares a `KIND`), or `:type("csv")` vs. `:type("xlsx")` (same function, different argument, no `KIND`) |
| SUBTRACT / INTERSECT | `values`/`values` | normal -- compare by each side's own `.data` (established behavior, unchanged) |
| SUBTRACT / INTERSECT | `paths`/`paths` | compare by identity (`path`+`uuid` together -- `path` alone is not always enough, e.g. CSVPATHS shares one `group.csvpath` path across every version) |
| SUBTRACT / INTERSECT | `values`(LHS)/`paths`(RHS) | RHS has no value to compare, so fall back to identity: compare LHS's own `path`+`uuid` against RHS's `path`+`uuid`. The *output* still carries LHS's own `.data` intact -- the comparison basis changed, the result shape (`values`) didn't. |
| SUBTRACT / INTERSECT | `paths`(LHS)/`values`(RHS) | **raise** ("bad query" -- LHS has no value to compare against RHS's), **unless RHS's accessor is specifically UUID-valued** (e.g. `:uuid()`, `:run_uuid()`), in which case LHS's own *native* `uuid` field (always present, no accessor needed) is compared directly against RHS's `.data` as a real uuid-to-uuid match. This is what makes "every named-file whose uuid intersects the named-file-uuids recorded across a set of runs" possible -- a genuine cross-datatype capability, not just an edge case. |

**UNION's compatibility rule is LHS-driven and purely structural**
(settled 2026-08-26, revised twice the same day -- first to an
intermediate "both sides' accessors must be literally identical" draft,
then to this one): if the left side is `paths` (no terminal `VALUE`-role
accessor at all), any right side unions freely, by path. Otherwise the
two sides must be comparable by *conceptual purpose*, not literal
accessor identity and not resolved-value type -- David's own framing:
"the accessor must equal. If it does, we then ask are the values
equal?" Two accessors are comparable if they share the same declared
`Function3.KIND` (e.g. `"uuid"` for `:uuid()`/`:run_uuid()`/
`:named_file_uuid()`/`:named_paths_uuid()`, `"name"` for
`:named_paths_name()`/`:named_results_name()`/`:named_file_name()`,
`"fingerprint"` for `:fingerprint()`/`:named_file_fingerprint()`/
`:file_fingerprints()` -- different functions, same conceptual family),
or if neither side declares a `KIND`, only if they are the literally
identical accessor (function name and argument together, via
`FunctionCall3.__eq__`) -- e.g. a bare `:type()` against another bare
`:type()`. Comparing the accessors' own conceptual purpose, not the
values they resolve to, is what decides comparability -- two
`values`-valued sides that ARE comparable may still resolve to
different actual values per item (two different `:uuid()` calls, or a
bare `:type()` on both sides); that is a downstream question for
whoever consumes the union, not something this check raises on.

Which functions share a `KIND` is a deliberately small, explicit list,
not inferred from resolved-value type or from which entity a field
belongs to -- David's own correction to an earlier draft of this note,
which had left the fingerprint functions uncategorized on the reasoning
that `:fingerprint()` (the FILES/CSVPATHS entity's own content) and
`:named_file_fingerprint()`/`:file_fingerprints()` (a RESULTS run's
*record* of a different entity's content) describe different entities.
David's correction: a fingerprint is a cryptographic identity of BYTES,
not of an entity or event the way a uuid is -- "same fingerprint" means
"same content" regardless of which manifest field recorded it or which
entity that field belongs to, so all three legitimately share `KIND =
"fingerprint"`. Concrete motivating case: two named-paths groups loaded
from identical `group.csvpath` text under different names get different
uuids but identical fingerprints -- comparing a group's own
`:fingerprint()` against a run's own record of which named-paths
content drove it (a field the Results Run Manifest does not carry yet,
but should -- see `deferred_work_bucket_list.md`) is exactly the kind of
comparison `:uuid()` cannot make. `:type()` is currently the only
function of its own conceptual purpose, so it still has no declared
`KIND`, and falls back to the literal-identity rule.

**Why SUBTRACT/INTERSECT's raise is asymmetric but UNION's isn't**: UNION
never compares resolved data at all, so its check is purely about not
mixing incompatible *accessors* into one bag -- it is LHS-driven because
the left side is what a caller is building the union *around*.
SUBTRACT/INTERSECT's asymmetry comes directly from *which side defines the
comparison basis*: a `values`-valued RHS demands a value to compare against
(LHS must have one too, or it's ill-posed); a `paths`-valued RHS only
demands identity, which every result always has, so LHS's own kind doesn't
matter.

---

## Architecture notes

`ReferenceExpression3` (`csvpath/references/reference_expression_3.py`) holds
`left`, `op` (`UNION`/`SUBTRACT`/`INTERSECT`), `right` -- each side is either a
plain reference string or another `ReferenceExpression3` (sub-expressions
nest freely). It works internally through `.resolve()` only -- there is no
meaningful `.query()`-only mode, since INTERSECT/SUBTRACT's join key is
resolved field-accessor data (`.data`), not something query-time path/uuid
alone can express. Output is a flat list of `ReferenceResults3`, the same
shape as a single reference's results -- each item keeps its own real
path/uuid/data intact, never collapsed down to just the key that made it
match.

Two building blocks this depends on:
- `ReferenceFinderFactory3.for_reference(*, reference, csvpaths)` -- parses a
  raw reference string and dispatches to the correct one of the three
  finders based on the parsed datatype.
- `ReferenceResults3.deduplicated()` -- collapses duplicates by
  `ReferenceResult3`'s own full `__eq__`. `identity` is load-bearing here,
  not incidental -- it is what lets two CSVPATHS statement-range results
  (which share the same path/uuid, since CSVPATHS has no per-statement uuid)
  be told apart.

UNION uses only that equality -- no join-key logic at all. INTERSECT/
SUBTRACT need the two-sided reduction described under Semantics notes above
(right side to a key set, left side deduplicated by full equality only,
never by key).

---

## Status notes

Everything reference expressions originally needed has been built and
merged. The one substantive fact from that build worth keeping as a
requirement, not just history: **a plain reference string with
`root_major == '*'` must resolve end to end through `ReferenceExpression3`**
(`ReferenceFinderFactory3` &rarr; the right finder &rarr; `resolve()`), not
just work when a finder is hand-built directly -- this is reference
expressions' own most natural use case (searching across unknown groups/
runs on either side, not just already-known literal names), and is what
makes the "orders" example's `_left_side`/`_right_side` able to be plain
reference strings rather than needing a sub-expression workaround.



**A settled decision worth keeping, not just the compendium's own
FILES-only `*`-vs-`:all()` composite-key example**: RESULTS' `:all()` at
`root_major == '*'` has *two* wildcarded axes open at once -- which
named-results group, and which template value -- and naively extending
either of `:all()`'s two existing, uncontested meanings alone (pool by
template value only, or group by named-results group only) silently
conflates two different groups that happen to reuse the same template
value. Settled: partition by the **composite** `(named-results-group,
template-value)` key -- matches `FilesReferenceFinder3`'s own `'*'`+`:all()`
precedent exactly (there, `file_home` already embeds the named-file's name
as a path prefix, so partitioning by `file_home` already *is* a composite
key). The compendium's own FILES example never has this collision to
resolve, since FILES' worked example only ever has one axis open at a
time -- this is the RESULTS-specific case where both axes are open
simultaneously, and needs its own statement wherever `'*'` traversal is
documented.

