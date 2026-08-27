# Proposed Minimum Function Set for Manifest/Definition Field Access

Built directly on top of `manifest_keys_reference_v2.md` (tables 1-9). Goal:
the smallest set of references-v3 functions that gives an AI (or any user)
field-level access to every key worth exposing, favoring one shared,
context-dispatching function over many near-duplicate bespoke names,
consistent with how `:manifest()`/`:definition()` already dispatch on
`DATATYPES` to pick which JSON file to read. This is a proposal to react to,
not a decision — nothing here is built yet.

## Cross-cutting notes before the lists

- **RESULTS has three sub-scopes, not one.** Table 5 (run), table 6
  (instance), and table 7 (archive-ledger entry) are all `DATATYPES.RESULTS`
  but hold different, only-partly-overlapping fields. A shared function
  covering RESULTS needs to dispatch on scope, not just datatype. That
  dispatch mechanism (how a reference resolves to "this run" vs "this one
  instance within it") is a prerequisite this proposal assumes exists or
  will exist separately — it is not itself a field-accessor design question.
- **Unify by concept, not by literal key match.** Two fields can share a
  literal key name and mean different things (see `status` below, a false
  cognate). Two fields can have different literal key names and mean the
  same thing (`from` vs `origin_path`, your original example). The grouping
  below follows meaning, confirmed against the source in
  `manifest_keys_reference_v2.md`, not spelling.
- **Deprecated/vestigial fields get no function at all.** Building an
  accessor for a field we have already flagged for removal just gives it a
  second reason to be hard to remove later. Excluded entirely: table 5
  `uuid` and `named_file_fingerprint_on_file`; table 6
  `number_of_files_expected`/`number_of_files_generated`; table 7
  `base_path`.
- **Tables 2, 4, and 7 are not reachable by any finder today.** Building
  field functions for their content does not by itself solve that —
  something still has to be able to point at "the global arrivals ledger"
  before a function can read a field off it. Flagged per-concept below
  where relevant, not solved here. (Table 6 was in the same boat when this
  note was first written; settled 2026-08-09 — a specific instance is now
  addressable externally via a named-paths group root_major, a run
  selector, and an instance identity, so it is dropped from this list.)

## Entity resolution and pooling — the formalized `*` rule

Settled 2026-08-07, arising from the `$*.files.:manifest()` question. This
governs every function in Parts A/B below, plus the new path-accessor
category, so it is stated once here rather than repeated per row.

**Rule 1 — whole-resource content accessors always resolve to exactly one
entity, full stop, no exceptions.** `:manifest()`, `:definition()`, and the
well-known-file content functions (`:errors()`, `:vars()`, `:meta()`,
`:data()`, `:unmatched()`, `:file()`) never pool raw content across more
than one named-file version, named-paths group version, run, or instance.
Entity resolution is singular and recursive: to reach a Result Instance
Manifest (table 6) you must resolve to one run *and* one instance within it
— `:all()` at either level, combined with a content accessor, is illegal;
so is a version-selecting reference that matches more than one version with
no pointer to pick between them, even for files/csvpaths' own manifest.json
(a single shared array across every version) where reading several matched
entries is comparatively cheap.

**Revision, 2026-08-07, same day:** this rule originally exempted "pooling
within one already-resolved entity's own version/run history" (e.g.
files/csvpaths' `:manifest()` with no pointer, several matched versions of
*one* named-file/group) on the grounds that it is cheap — one shared array,
already read, just sliced. David pushed back: that exemption ties legality
to a storage detail (does this entity type happen to keep its versions in
one shared file, or one file per version) rather than to what the reference
*means*. A cost-based carve-out is a leaky abstraction — the same syntax
could become legal or illegal if a future entity type's storage changes.
The corrected, adopted rule: **reading full content with a reference always
touches exactly one entity, regardless of how any given entity type happens
to persist its data today.** No carve-outs. If more than one thing would
otherwise match, a pointer or identity is required to pick one — same rule,
same wording, at every level, for every datatype. Implemented across files/
csvpaths (PR #229) and results, both run-level and instance-level (PR #222).
The "cheap search, then selective fetch" `query()`/`resolve()` split already
covers the "I want N of these" case without this rule's help — nothing is
lost by requiring one reference per entity when reading content.

**Rule 1a — the one exception is a real, existing global ledger, and it is
per-function.** `*` (or any other unresolved-entity position) at root_major
combined with a bare `:manifest()` resolves to that datatype's global
ledger — table 2 for FILES, table 4 for CSVPATHS, table 7 for RESULTS —
because exactly one such single resource genuinely exists per datatype.
`:definition()` has no equivalent global ledger anywhere in the codebase, so
`$*.files.:definition()` (or the CSVPATHS equivalent) is **not legal** —
enforced by the function/finder layer raising, the same way the existing
`Star3` root_major check already raises today, not by the grammar. The
grammar stays permissive on purpose (see `reference_grammar_3.py`'s own
notes on deferring datatype-specific semantic checks out of the grammar);
this is one more instance of that same split, not a new exception to it.

**Rule 2 — path accessors are exempt from Rule 1 and are always poolable
(RETIRED 2026-08-26).** `:path()`, built per this rule, wrapped any
whole-resource content function and returned the filesystem path to that
resource instead of its content. Retired once Rule 1's own enforcement moved
from `query()` to `resolve()`/`resolve_from()` (see the `deferred_work_
done_list.md` entry) — `:path()` existed only to route around `query()`-time
enforcement (a path is cheap/poolable, so wrapping a content function in
`:path()` let a caller get *that*, sidestepping the single-entity gate the
content function itself would hit). Once the gate itself moved to
`resolve()` and `query()` became unconditionally allowed to return multiple
matches regardless of accessor, the same job is just `query()` on the
ordinary content accessor directly, without resolving it — no wrapper
function needed. `Path3`/`wrappers/path_3.py` removed; `_find_path_call`/
`_resolve_path_call` removed from `ReferenceFinder3`.


**Rule 3 — field/key accessors (Part A and Part B below) are also exempt
from Rule 1 and are always poolable**, for the same reason as Rule 2: a
single field's value is a cheap scalar (or a small fixed-shape value, e.g.
`file_fingerprints`'s dict), not a raw structure to merge. `$*.files.:uuid()`
is legal and returns a list of uuids, one per version of every named-file
matched — the cross-product of the entity axis (`*`) and the
unreduced-within-entity version/run axis, per the existing convention. This
is exactly the case Rule 1 exists to prevent for whole-resource content:
the same cross-product with full manifest dicts instead of scalar uuids is
the expensive, unwieldy case that motivated Rule 1 in the first place.

## Part A — Shared, context-dispatching functions

One function name, `DATATYPES`/scope decides which literal key it reads.

| Function | Datatypes / scopes | Key mapping | Notes |
|---|---|---|---|
| `:uuid()` | FILES, CSVPATHS, RESULTS (instance) | FILES → table 1 `uuid` (table 2 `uuid` same, ledger unexposed); CSVPATHS → table 3 `uuid` (table 4 same, unexposed); RESULTS instance → table 6 `uuid` | At RESULTS run scope this coincides with `:run_uuid()` below — table 5's own bare `uuid` is the excluded, vestigial one. |
| `:run_uuid()` | RESULTS (run, instance, archive-ledger) | table 5 `run_uuid`; table 6 `run_uuid`; table 7 `run_uuid` | "Which run does this belong to," distinct from `:uuid()`'s "this entity's own id" — the distinction only matters below run scope. |
| `:time()` | FILES, CSVPATHS, RESULTS (all 3 scopes) | table 1/3/5/6/7 `time`, same literal key everywhere | Cleanest case in the catalog — no renaming needed anywhere. |
| `:time_completed()` | CSVPATHS, RESULTS (run) | table 3 `time_completed`; table 5 `time_completed` | Not applicable to FILES. Table 3's own description already notes it is rarely useful (loads are quick). |
| `:fingerprint()` | FILES, CSVPATHS | table 1 `fingerprint` (file bytes); table 3 `fingerprint` (`group.csvpaths` text) | Deliberately NOT unified with table 5 `named_file_fingerprint` or table 6 `file_fingerprints` — those describe the fingerprint of *other* content this result consumed/produced, not of the entity itself. Same S3-MD5 caveat applies everywhere per the catalog. |
| `:manifest_path()` | CSVPATHS, RESULTS (run, archive-ledger) | table 3 `manifest_path`; table 5 `manifest_path`; table 7 `manifest_path` | Gap: not a stored field for FILES (table 1) or RESULTS instance (table 6) today — would have to be computed from the registrar rather than read if wanted there. |
| `:home()` | FILES, CSVPATHS, RESULTS (run, instance) | table 1 `file_home`; table 3 `named_paths_home`; table 5 `run_home`; table 6 `instance_home` | The raw manifests already use a consistent `_home` suffix for this concept across all four — strong natural fit for one name. |
| `:origin()` | FILES, CSVPATHS | table 1 `from` (table 2 `origin_path`, same concept, unexposed); table 3/4 `source_path` | Your original `from`/`origin_path` example. Deliberately NOT the same concept as table 6 `origin_data_file` (see Part B) — that is about which physical file *this run* actually read, not where the registered content originally came from. |
| `:reference()` | FILES | table 1 `reference` (table 2 same, unexposed) | Gap: no equivalent stored field for CSVPATHS or RESULTS today. Giving those the same denormalized-reference convenience would mean adding a field to the schema, not just a function — a main-codebase question, not just a references-v3 one. |
| `:hostname()` / `:username()` | RESULTS (run) | table 5 `hostname`/`username` | Same fields exist in tables 2/4 (unexposed ledgers) with real values. Not proposing `:ip_address()` — it is confirmed always-null everywhere (the lookup is disabled); a function that always returns null is not worth building until that is fixed. |
| `:identity()` | RESULTS (instance, archive-ledger) | table 6 `instance_identity`; table 7 `identity` | Same concept, different literal key — another `from`/`origin_path`-style case. |
| `:serial()` | RESULTS (run, instance) | table 5 `serial`; table 6 `serial` | Identical meaning, identical key, both scopes. |
| `:valid()` | RESULTS (run, instance) | table 5 `all_valid` (aggregate across the group); table 6 `valid` (this one instance) | Same concept at two aggregation levels — scope alone picks the right key. |
| `:completed()` | RESULTS (run, instance) | table 5 `all_completed`; table 6 `completed` | Same pattern as `:valid()`. |
| `:files_complete()` | RESULTS (run, instance) | table 5 `all_expected_files`; table 6 `files_expected` | Same concept, different literal key, same aggregate/instance split as `:valid()`/`:completed()`. Name deliberately avoids reusing either source key, since both are slightly misleading in isolation per the catalog notes. |
| `:named_paths_name()` / `:named_file_name()` / `:named_results_name()` | RESULTS (run, instance, and CSVPATHS self-reference for the first) | table 3/5/6/7 as applicable, consistent literal keys throughout | Cross-references to which named-paths group/named-file/named-results this entity belongs to — not the same thing as a bare "what is my own name," so no conflict with the existing `:name()` context-setter. |

## Part B — Dedicated, single-context functions

No recurrence elsewhere in the catalog; a shared name would just be a
single-context function wearing a generic label.

| Function | Datatype / scope | Key(s) | Notes |
|---|---|---|---|
| `:mark()` | FILES | table 1 `mark` | Excel worksheet name. |
| `:template()` | FILES, CSVPATHS, RESULTS (run, archive-ledger), and both definition.json schemas | table 1/3/5/7 `template`; table 8/9 `template` | Recurs by literal key everywhere, but deliberately kept out of Part A: table 9's `template` is the live source of truth, table 3/5/7's `template` are historical snapshots of it (per the catalog). One function, but the *meaning* differs by which manifest answers it, which is a sharper distinction than the other Part A entries — worth its own row so that distinction stays visible rather than getting flattened into a generic mapping table. |
| `:source_mode_preceding()` | RESULTS (instance) | table 6 `source_mode_preceding` | |
| `:preceding_instance_identity()` | RESULTS (instance) | table 6 `preceding_instance_identity` | Carries the issue #223 caveat forward — should say so in its own `SUMMARY`. |
| `:actual_data_file()` / `:origin_data_file()` | RESULTS (instance) | table 6 `actual_data_file` / `origin_data_file` | Kept as a pair since they only mean anything in contrast to each other. |
| `:transfers()` | RESULTS (instance), and named-paths definition.json | table 6 `transfers`; table 9 `transfers.path_transfers` | Carries the #224 and #226 caveats forward. |
| `:file_fingerprints()` | RESULTS (instance) | table 6 `file_fingerprints` | Dict-shaped (per generated file), not a scalar — structurally different from `:fingerprint()`. |
| `:method()` | RESULTS (run) | table 5 `method` | |
| `:status()` | RESULTS (run) | table 5 `status` | Do not reuse this name or mapping for table 2's `status` — same key, different concept (a failure message, not a lifecycle marker). If table 2 ever gets exposed, that needs its own name. |
| `:named_paths_identities()` / `:named_paths_count()` | CSVPATHS | table 3 `named_paths_identities` / `named_paths_count` | |
| `:on_arrival()` | FILES definition.json | table 8 `on_arrival` (whole object) | Almost certainly your `:activation()`. |
| `:sources()` / `:destinations()` | FILES / CSVPATHS definition.json | table 8 `sources`; table 9 `destinations` | Same `ServerConfig` shape both places; kept as two names since one is about where a file is polled from and the other where a group sends things — different direction, easy to confuse if merged. |
| `:scripts()` / `:webhooks()` | CSVPATHS definition.json | table 9 `scripts`; table 9 `webhooks` | Whole-object accessors, mirroring `:transfers()`'s relationship to `path_transfers`. |

## Part C — Excluded outright

Table 5 `uuid`, table 5 `named_file_fingerprint_on_file`, table 6
`number_of_files_expected`/`number_of_files_generated`, table 7 `base_path`.
No function proposed for any of these.

## Part D — Open gaps found while building this list

- `:reference()` has no CSVPATHS/RESULTS equivalent field to read (noted in
  Part A) — an add-a-field question, not a references-v3 question.
- ~~`:manifest_path()`/`:home()` are unavailable as *stored* fields for a
  couple of scopes (FILES' own manifest_path; RESULTS instance's
  manifest_path) — computable from the registrar, just not present in the
  JSON today.~~ Settled 2026-08-09 and removed: RESULTS instance's
  manifest_path was found to already be stored and reachable while
  building batch 3 (Part A/B), contradicting this note at the time it was
  written; FILES' own manifest_path was a real gap, fixed via #237.
  `:home()` never had a cited gap beyond these two manifest_path examples,
  so nothing outstanding remains here.
- Table 6's `error_count`: `ResultRegistrar.register_complete()` computes
  `mdata.error_count = self.result.errors_count`, but
  `metadata_update()` never writes it into the instance manifest JSON — set
  on the object, never persisted. Same shape of bug as #224. Filed as #227.
- Exposing tables 2, 4, and 7 at all is blocked on addressing, not on field
  access — worth its own design pass before any of Part A's ledger mappings
  can actually be reached through a real reference. (Table 6 was originally
  included here too; settled 2026-08-09 and removed — see the cross-cutting
  note above.)
