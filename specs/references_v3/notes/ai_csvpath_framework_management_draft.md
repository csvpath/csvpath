# AI Guide to Managing a CsvPath Framework Project (DRAFT)

> **Status:** first-pass draft, not a finished spec. Assembled by scanning
> FlightPath's in-app help content (`flightpath/assets/help/` and
> `flightpath/assets/examples/`) as a headstart for a proper AI-facing
> operations/management reference. Expect to edit and expand heavily.
> Long-term home is undecided — it may end up living in a `flightpath_generator`
> project (AI features) once that project exists, rather than here in
> `csvpath/docs/`. This draft is written for a reader that already understands
> generic data-pipeline concepts and CsvPath Framework's References language
> (v1/v2 and the v3 initiative), so it does not re-explain those basics.

## 1. The core storage model

CsvPath Framework organizes a project around three named collections, each
backed by pluggable storage (local filesystem, S3, Azure Blob, GCS, or SFTP):

- **named-files** — a logical name (e.g. `orders`) for data that changes over
  time as new physical files arrive. The name is stable even though the
  underlying file name/location/content changes month to month. Each
  named-file can have many versions, arriving under different physical names
  at different times. The bare name always points to the most recently
  arrived version; a **reference** is required to reach any other version.
- **named-paths** — a named group of one or more CsvPath Language statements
  (csvpaths) that validate and/or upgrade data. Groups are run as a unit
  against a named-file. Breaking logic into multiple simple statements,
  rather than one large statement, is the recommended style.
- **named-results** (the **archive**) — the immutable output of running a
  named-paths group against a named-file: one run. Results are the "trusted
  publishing space" — the internal source of truth for downstream data
  consumers, and the thing an AI is most often asked to reason about
  forensically ("what happened," "was this run good").

A **run** pairs one named-paths group with one named-file (or a specific
version/subset reachable via a reference) and produces a directory of
artifacts in the archive (see §3).

Both named-files and named-paths groups support **templates** — path patterns
using `:N` tokens (0-based segment index from the *original* arrival path) and
datetime tokens (`:year`, `:month`, `:month_name`, `:day`, `:hour`,
`:hour_24`, `:minute`, `:second`) to control where staged files or run results
land. named-file templates end in a mandatory `:filename` token; named-paths
templates end in a mandatory `:run_dir` token (the run's timestamped home
directory, which holds `manifest.json` and the individual csvpath
subdirectories). Templates are optional — most projects work fine without
them — but when present they explain *why* a given archive/staging path looks
the way it does, which matters when tracing where a specific version landed.

## 2. Runs: methods, sourcing, and how csvpaths relate within a group

A named-paths group can be run four ways, along two independent axes:

- **Serial vs. breadth-first** — serial applies each csvpath statement to all
  of the data in turn, one statement finishing before the next starts.
  Breadth-first (the `_by_line` methods: `collect_by_line()`,
  `fast_forward_by_line()`, `next_by_line()`) matches each *line* against
  every statement in the group before moving to the next line, letting each
  statement modify the line before passing it on.
- **Collect vs. fast-forward** — collect captures the data of each matching
  line; fast-forward captures nothing but still produces metadata, error
  handling, and printouts. Fast-forward runs never produce `data.csv`.

Within a group, a csvpath's **source-mode** determines whether it reads the
original named-file data (the default) or the *output of the preceding
csvpath* in the group — the other way (besides breadth-first) to chain
statements together.

A csvpath can be excluded from its group's run entirely via **run-mode:
no-run** (default is `run`) — useful for temporarily disabling one statement
in a group without removing it.

## 3. What a run produces, and how to tell if it went well

This is the section most directly useful for forensic/audit questions ("did
last night's runs succeed," "what broke"). Every run generates these files
in its archive directory **regardless of settings**:

- `manifest.json` — the run's record, including the UUIDs of the inputs to
  the run for back-tracing.
- `meta.json` — user- and framework-defined metadata (see below), plus a
  `file_name` field naming the named-file source (distinct from the runtime
  `file_name` print field, which is the physical path of the file actually
  used).
- `vars.json` — the csvpath's variables (`@name`) at end of run.
- `errors.json` — collected error objects (present if `validation-mode`
  includes `collect`, which is the default).

Generated conditionally, controlled by **files-mode** (`all`, `data`/
`no-data`, `unmatched`/`no-unmatched`, `printouts`/`no-printouts`):

- `data.csv` — matching lines (collect runs only; never present for
  fast-forward runs). If `files-mode` expects a file type that wasn't
  actually produced (e.g. `data` expected but the run was `fast_forward`, or
  `unmatched` expected but `unmatched-mode` was `no-keep`), the **metadata
  will flag the mismatch** — a direct machine-checkable signal that a run's
  configuration and its actual behavior disagree.
- `unmatched.csv` — unmatched lines, only if `unmatched-mode: keep` was set
  (default is `no-keep`, i.e. discard).
- `printouts.txt` — everything sent via `print()`/`error()`, grouped in
  blocks per named Printer stream or separated into individual files named
  by their print stream name if the csvpath sets `print-mode:separate`.

**Signals of a bad or off-nominal run, in roughly increasing cost to check:**

1. **`meta.json` → `valid` / the `$.csvpath.valid` runtime field** — false
   only if the csvpath author called `fail()`, or an error occurred *and*
   `validation-mode` includes `fail`, or `validation-mode` includes `fail`
   *and* config's error settings would also fail. Otherwise a file is
   considered valid by default — i.e. **absence of explicit failure signals
   is not proof of a clean run**; a csvpath author must have opted in to
   marking failure for `valid` to mean much. Conversely, the presence of
   errors does not automatically indicate a failed run, since some errors,
   especially built-in validation errors, may be expected under certain
   circumstances.
2. **`meta.json` → `stopped` / `$.csvpath.stopped`** — true if the run was
   halted mid-way (via `stop()`, `validation-mode: stop`, which halts at an
   invalid line without guaranteeing the current line finished evaluating,
   or when `validation-mode:raise` and either an `error()` or a built-in
   validation error occurs, which raises an exception and stops immediately
   with a stack trace in the log).
3. **`errors.json`** — the collected error objects for the run (present when
   `validation-mode` includes `collect`, the default). Each error's message
   pattern includes: `time`, `file`, `line` (0-based), `paths` (group name),
   `instance` (statement identity or index), `chain` (idchain to the failing
   match component), `message`.
4. **Unmatched-line volume** — `unmatched.csv` (if kept) or the
   `lines_collected` vs. `total_lines` runtime print fields, or
   `count_matches` vs `count_scans`, as a proxy for how much data a run
   rejected.
5. **`printouts.txt`** — free-text signal; may contain ad hoc validation
   messages an author printed deliberately, in addition to (or instead of,
   if `print-mode: no-default` suppressed console/default output) built-in
   error printouts.
6. **The CsvPath Framework log** — level-driven (`DEBUG`/`INFO`/`WARN`/
   `ERROR`); `explain-mode: explain` (expensive, ~20-25% overhead) dumps a
   step-by-step account of every match decision to `INFO`, useful for deep
   debugging a specific line/statement but not something to enable broadly.

**Important nuance repeatedly stressed in the source material:** CsvPath
Framework does not itself decide whether a *match* means "valid." Matching
is pure predicate logic (`logic-mode: AND` or `OR` across match components
that have as much in common with SQL DML and Schematron as with a schema
language like XSD or DDL). Validity, or not, and failure, or not, are
decisions the *csvpath author* encodes explicitly (via `fail()`,
`validation-mode`, guard qualifiers, etc.) — so answering "did this run
indicate a problem" requires knowing what that group's authors actually
wired up as failure signals, not just querying a fixed schema field.

In some cases a csvpath statement writer may document in their named-paths
group's README.md file useful information about how they are determining
validity and failure. README.md is generated for both named-files and
named-paths and when in doubt should be checked for helpful information.

**Error-handling channels** (configured globally in `config.ini`'s `[errors]`
section, overridable per-csvpath via `validation-mode`): `log`, `print`,
`collect` (→ `errors.json`), `raise` (halts immediately, most internal detail,
least ops-friendly), `stop` (graceful halt), `fail` (marks run failed,
no other effect). `validation-mode` is an *overlay* on the global config —
negate an inherited setting with a `no-` prefix (e.g. `no-raise`).

## 4. Manifest types: the real schema (confirmed by controlled experiment, 2026-07-25)

Section 3 above was written from FlightPath's UI help text, which never gives
exact machine shapes. This section replaces that guesswork with findings
confirmed by scripting the real `csvpath` library directly (source, not
docs) and running deliberate scenarios. There are **7** `manifest.json`
types in the real system:

1. **All registrations** — a project-wide index of every named-file,
   named-paths group, and named-results archive registered. Not yet
   directly inspected field-by-field — confirm shape before relying on it.
2. **Each named-file** (`file_registrar.py`) — one array entry per physical
   version registered under that name. **Confirmed:** `named_file_fingerprint`
   (SHA256) reliably identifies exactly which version a run consumed, even
   once a named-file has multiple registered versions.
3. **All named-paths groups** — a project-wide index of every named-paths
   group. Same caveat as #1: not yet directly inspected.
4. **Each named-paths group** (`paths_registrar.py`) — a JSON array, one
   entry per load/reload. **Confirmed idempotent:** reloading byte-identical
   content is a no-op, no new entry. **Confirmed replace vs. append:**
   `add_named_paths(append=...)` is a real API parameter — `append=False`
   (default) replaces the live statement set (new entry's `named_paths` is
   *only* the new content); `append=True` merges old+new (new entry's
   `named_paths` is a strict superset containing the prior entry's exact
   text verbatim). This means replace-vs-append is discriminable from the
   data alone — test containment between adjacent array entries — without
   needing to know which API call produced a given entry.
5. **All runs** (`run_registrar.py`) — archive-root ledger, one
   ever-growing array of every run in the project, minimal fields, built
   for discovery/enumeration rather than per-run detail.
6. **Each named-result / each run** (`results_registrar.py`) — a single
   dict at `run_home` root. This is the manifest with `all_valid`,
   `error_count`, `named_paths_uuid`, `named_file_fingerprint`, etc.
   **Confirmed — corrects an earlier hypothesis of ours:** `named_paths_uuid`
   is a **direct UUID match** to one specific entry inside that named-paths
   group's own manifest array (type #4), not the group as a whole, and not
   resolved by timestamp inference. The matching entry's array index is the
   version index the references-v3 spec refers to for csvpaths versioning.
7. **Each csvpath instance within each named-result** (`result_registrar.py`)
   — one level deeper than #6, its own `valid`/`errors_count`/
   `file_fingerprints` per statement identity within the run.

**Still open:**
- Types #1 and #3 (the two project-wide "all X" indexes) were inferred to
  exist, not directly inspected — confirm their field shapes before an AI
  relies on them for cross-project enumeration.
- A genuinely **stopped/incomplete** run (via `validation-mode: stop`, not
  the `stop()` function) was not captured in this round — every test run
  completed (`stopped: false`). The `valid`-vs-`stopped` distinction in §3
  above is the current best understanding but is unconfirmed by a real
  stopped-run example.
- **Caution, not yet understood:** in this experiment, every scenario after
  the second named-paths load executed **twice**, ~21 seconds apart,
  byte-for-byte identical (doubling manifest entries and run directories).
  Cause unknown; didn't corrupt the findings above (duplicates just
  confirmed each other), but it means raw run *counts* or manifest *array
  length* are not yet trustworthy signals for anything audit-related until
  this is understood.

## 5. References (v1/v2 — the user-facing form)

*(For contrast with the v3 initiative; this section describes what users and
existing tooling see today.)*

Both `files` and `results` reference types share the same shape:

```
$name.datatype.selector:limiter:limiter.optional-second-selector:limiter:limiter
```

- **datatype** is `files` or `results`.
- **selector** matches by date (`YYYY-MM-DD_HH-MM-SS`, prefix-matched, must
  start with 4+ digits and a dash), path (prefix-matched, relative to the
  named-thing root), or — for `files` only — an exact-match SHA256
  fingerprint of the file's bytes; for `results`, a csvpath identity/ID
  (exact match).
- **limiters** (0–2 per selector) are one of:
  - *Ranges*: `all`, `before`, `to`, `after`, `from`, `yesterday`, `today`
  - *Ordinals*: `first`, `last`, `index`
  - *Dates*: same form as a selector date, also prefix-matched
  - *(results only)* Data-file limiters: `data`, `unmatched`

`results` references additionally support a second selector position for a
csvpath identity, so you can drill from "a run" down to "one statement's
output within that run" (e.g. `$orders.results.may/acme:first().EMEA`).

`csvpaths` references (for selecting which statements a run applies) let you
pick a starting/ending statement by index or ID, e.g. `2:from` or
`readings:to`.

Reference types not covered above, used inside `print()` only:
`csvpath` (runtime stats of the executing statement — see §3's print-field
list), `headers` (current line's header values), `variables` (the
`@`-prefixed variable namespace — currently only the *most recent* past run's
variables are reachable this way), `metadata` (fields set in an external
comment, i.e. `~ name: value ~` before a statement).

## 6. csvpath statement vocabulary (for reading transformation logic, not writing it)

- **`$`** — anchor of every reference (to named-files/paths/results, inside
  `print()`, or as function input).
- **`#header_name`** — accesses a header's value for the current line.
- **`~ ... ~`** — an external comment, holding metadata fields (`word:` form)
  including all the *modes* below. Comments before the statement are far more
  common than after.
- **`->`** (when-do) — CsvPath's if-statement: right-hand side executes only
  when left-hand side is true, without necessarily affecting match status
  (especially combined with the `nocontrib` qualifier).
- **`==`** — equality test, usable as a match component or as input to
  another function.
- **`+` / `*` in scan instructions** (the statement's first bracket) — `+`
  adds specific lines to scan (e.g. `3+5` = scan the 4th line, 0-based);
  `*` matches all remaining/all lines.
- **`ID`/`Id`/`id`/`NAME`/`Name`/`name`** metadata field — gives a statement
  within a group a human identity, shown in errors, logs, references, and
  output files instead of a bare index.
- **Qualifiers** (attached to match components) worth knowing when reading
  statements: `notnone` (disallow None, like `NOT NULL`), `distinct` (must be
  unique), `once` (evaluate exactly once, then behaves like `nocontrib`),
  `nocontrib` (never affects match decision — used for pure side effects),
  `onmatch` (only fires once all other components agree the line matches;
  evaluated in *reverse* order among components that have it), `onchange`
  (fires when value changes line-to-line), `renew` (reset every line),
  `latch` (freeze after first set), `increase`/`decrease` (guard, not
  validation — silently blocks the wrong-direction change rather than
  erroring), `strict` (require decimal point on decimals; reject one on
  integers), `tmp` (exclude a variable from `vars.json`, e.g. for large
  values).
- **Modes** are metadata fields that configure run/error behavior per
  statement (all detailed in §3 above, plus): `transfer-mode` (copy
  `data.csv`/`unmatched.csv`/named result files to an arbitrary configured
  location post-run, without touching the immutable archive copy —
  equivalent to but simpler than named-paths-group-level Transfers config),
  `return-mode` (`matches` (default) vs `no-matches`, i.e. whether `next()`/
  `collect()` return matched or unmatched lines).

## 7. Supporting configuration concepts

- **`config.ini`** sections: `cache`, `config` (self-referential reload
  path), `errors`, `extensions` (what counts as a data file), `inputs`
  (where named-files/named-paths live), `listeners` (integrations),
  `logging`, `results` (archive + transfers). `CSVPATH_CONFIG_PATH` env var
  or `[config] path` can redirect to a non-default config location (reload
  cycles are detected and refused at startup).
- **Integrations/listeners**: storage backends (S3/Azure/GCS/SFTP) vs.
  event-driven metadata consumers — webhook, scripts, sql, sqlite, default,
  otlp (OpenTelemetry), sftp, sftpplus, ckan, marquez (OpenLineage), slack.
  Enabled via the `[listeners] groups` comma-list; most require per-csvpath
  configuration as well as their listener group enbled.
- **Webhooks** — fire on 4 conditions (any run / all-valid / any-invalid /
  has-errors); POST a JSON payload built from `name > value` pairs, where
  `value` can be a literal, `meta|field`, `var|field`, or an ALL-CAPS env var
  substitution.
- **Scripts** — fire on 4 conditions (any run / all-valid / any-invalid /
  has-errors). Scripts carry security issues that make them less favored in
  general and not available in FlightPath Server without special admin config.
- **Transfers** (group-level config, distinct from per-statement
  `transfer-mode`) — grouped by statement + end-state (all / valid / invalid
  / errors), can target any configured backend, and can reference standard
  output files by short name: `data`, `vars`, `errors`, `unmatched`, `meta`,
  `printouts`, `manifest`.
- **Date offsets** — a FlightPath Data (client) -only testing feature to make
  the tool believe it's a different day (session-scoped, never persisted) —
  relevant only if you're told a discrepancy might be an artifact of this,
  not a real production behavior.

## 8. Known gaps this draft does NOT close

Section 4 closed the biggest original gap (provenance, replace-vs-append,
manifest shapes) via a controlled experiment against real library code. What
remains open, as of 2026-07-25:

- The two project-wide "all X" manifests (types #1 and #3 in §4) —
  existence inferred, fields not yet inspected.
- `meta.json`'s full field list beyond `valid`, `stopped`, `file_name`, and
  the `runtime_data` block observed in testing (headers, scan/match counts,
  mode settings) — likely more fields exist, unenumerated so far.
- The exact shape of `vars.json` when a csvpath actually assigns `@variables`
  — only observed as `{}` so far (test statements didn't assign any).
- A real **stopped/incomplete** run example (`validation-mode: stop`) —
  `stopped` was `false` in every run tested; the `valid` vs. `stopped`
  distinction in §3 is design-doc-level understanding, not yet confirmed
  against a real stopped run's actual files.
- The unexplained **double-run** behavior noted at the end of §4 — doesn't
  invalidate anything confirmed there, but raw run counts/manifest array
  length shouldn't be trusted for audit purposes until it's understood.
- Webhooks write a send record into the named-results run_dir that hasn't
  yet been explored. Transfers do not currently log their activity other than
  to the `csvpath.log` file on INFO.

Closing these requires more controlled experiments (as in §4) or reading
CsvPath Framework source directly — not more FlightPath help content, which
has now been fully mined for what it can offer.
