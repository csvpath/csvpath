# Normative Examples Coverage Matrix — §6 Functions + Manifest Functions

Purpose: for each function/rule the compendium (`references_v3_compendium.md`)
and `references_v3_required_manifest_functions.md` assert, does
`normative_reference_examples.txt` actually demonstrate it? This is a
different axis from `function_coverage_matrix.md` (function → unit-test
coverage against the code registry). This one tracks spec requirement →
normative example, so we can see where the *spec* is thin on worked
examples, independent of what's built. Hand-maintained; re-check after any
of the three docs changes materially.

§6 (Functions) and `references_v3_required_manifest_functions.md` done.
§3/§4/§5 (Reference Model, Wildcards, Query vs Resolve) not yet done —
next pass.

## Status as of 2026-09-05 (third pass — all prior §6 items resolved)

All items from the first two passes are resolved:
- `:false()` example fixed (was copied from `:true()`).
- `:none()` example now uses `:completed()`, matching the established field name.
- The `:empty()`/`:none()` comparison table's markdown is fixed.
- `:before()`/`:after()`/`:log()` now demonstrated across all three datatypes (were single-datatype/THIN).
- `:now()` and `:above()`/`:below()` are used in examples — still not in the compendium's own §6.34/§6.36 enumeration, but per §6.10-6.11 the compendium deliberately defers the full field/predicate-function list elsewhere, so this is lower priority than it first looked.
- `:template()` / FILES-level `:status()` — confirmed legitimate against `references_v3_required_manifest_functions.md` (see below). No compendium change needed; §6.10-6.11 already defers enumeration of manifest-derived field accessors to that doc.
- `:choice()`'s "mooted" status in compendium §3.9c is still open — not addressed this pass, still worth a decision.

## `references_v3_required_manifest_functions.md` review

### `:home()` — resolved

Doc now carries an explicit note: `:home()` solely means the field accessor
retrieving a named-entity's *own* home path; relationships to *other*
entities use specific names (`:named_file_home()`, `:run_home()`,
`:named_paths_home()`, etc.). This matches `function_coverage_matrix.md`'s
existing classification (role: `value`, "field accessor... rides beside
the matched entity's own pointer") and resolves the ambiguity with the
retired name_one-wildcard sense of `:home()` from earlier in this session.
Settled — no further action.

### Two remaining naming inconsistencies in this doc (not yet addressed)

- **`named_paths_identities`/`named_paths_count` fields map to
  `:identities()`/`:identities_count()`** in the doc's own tables (Named-
  Paths Manifest rows), but the actually-built, tested, and normatively-
  used names everywhere else are `:named_paths_identities()`/
  `:named_paths_count()`. The doc's table is stale — should be corrected to
  match reality.
- **`:archive()` is inconsistent with itself across two schemas.** In the
  Archive Run Manifest, `:archive()` = the archive *path* and
  `:archive_name()` = the archive *name* — a sensible split. But the Named-
  Paths Manifest's own `archive_name` field (a name, per its own
  description) maps to `:archive()` — the "path" function by the other
  schema's convention. Looks like it should be `:archive_name()`.

### One typo

- `source_mode_preceding` field → `:source_mode_preceeding()` (extra "e")
  — misspelled, sitting right next to the correctly-spelled
  `:preceding_instance_identity()` in the same table.

### Coverage sweep (82 distinct functions named in the doc)

36 have real normative-example coverage (mostly the widely-used manifest
fields: `:manifest()`, `:uuid()`, `:fingerprint()`, `:type()`,
`:named_file_name()`, `:serial()`, `:error_count()`, `:time()`,
`:completed()`, `:valid()`, `:status()`, `:file()`, etc.).

The remaining ~46 have zero normative coverage. Almost all fall into two
low-priority buckets rather than being individually concerning:

1. **Low-level path/location accessors** — `:file_path()`, `:file_name()`,
   `:archive()`, `:archive_name()`, `:named_files_root()`,
   `:named_paths_root()`, `:group_file()`, `:group_manifest()`,
   `:file_manifest()`, `:reference()`, `:source()`, `:named_file_path()`,
   `:named_file_size()`, `:named_file_last_change()`, `:host()`,
   `:instance_index()`, `:identity()` (has 1), `:run_dir()`.
2. **Deeply-nested definition.json sub-object accessors requiring a name
   argument** — `:script_on_complete_all/valid/invalid/error()`,
   `:webhooks_on_complete_all/valid/invalid/error()`,
   `:transfer_on_complete_all/valid/invalid/error()`,
   `:source_address/port/username/password(str)`,
   `:destination_address/port/username/password(str)`,
   `:named_paths_group()`, `:run_method()`.
3. **Lifecycle fields with an established sibling already covered** —
   `:all_completed()`, `:all_valid()` (siblings `:completed()`/`:valid()`
   already have examples at instance scope; these are the run-wide
   aggregate versions and have none).

None of these are wrong — they're undemonstrated, mechanical field lookups
rather than distinct behavioral rules, so lower priority than the §6 gaps
were. Worth eventually giving each at least one line, but not urgent
before returning to implementation.

## Priority list going into the next pass

1. Fix `:named_paths_identities()`/`:named_paths_count()` naming in
   `references_v3_required_manifest_functions.md`'s tables (stale vs. reality).
2. Fix `:archive()`/`:archive_name()` inconsistency (Named-Paths Manifest
   row should be `:archive_name()`).
3. Fix `:source_mode_preceeding()` typo → `:source_mode_preceding()`.
4. Resolve `:choice()`'s mooted-vs-real status in compendium §3.9c.
5. Add at least one example each for `:all_completed()`/`:all_valid()`
   (run-wide aggregates) — cheap, closes a real small gap.
6. Everything else in the zero-coverage list — batch/backlog, not urgent.
