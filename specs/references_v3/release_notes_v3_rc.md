# References v3: release notes for the release candidate

Draft, 2026-11-17, for David to edit. "Before" is the last release, v0.0.631 (tagged 2026-10-22), and the notes cover the references language (`$name.datatype.name_one.name_three`), reference expressions, and the ledgers and SQL mirror behind them. CVL matching-function changes are covered separately.

## Removed functions

These raise now:
- **`:home()`** (#504). The replacements:
  - `$alpha.results.:home()` (the zero-level runs) becomes `$alpha.results.:all()` or `:from(0)`;
  - `$*.results.:home()` becomes `$*.results.:from(0)`;
  - `$*.files.:home():definition(...)` becomes `$*.files.:definition(...)`;
  - a FILES name_one `:home()` never matched a real registration (it gave `[]`), so write the path without it.

  RESULTS raises "Unknown reference function: home"; FILES gives its usual rejection of an unknown name_one function.
- **`:none()`, `:not_none()`, `:empty()`, `:not_empty()`** (#509). Use `:has_value()` and `:does_not_have_value()` instead. A field has a value when it holds a primitive, including `0` and `false`, or a non-empty list or dict. Every field matches exactly one of the two.
- **`:files_complete()`** (#671), "Unknown reference function". It is disabled: the manifest flags behind it are not reliable yet.

## Ledger values that changed

- **Every named-files and named-paths ledger entry has an explicit `status`** (#456). A registration or load used to have none on success; it now writes `complete`. A failed FILES registration writes `failed` instead of `Registration failed`. A `:status("Registration failed")` filter needs updating. Entries written before this release have no `status`, so they match no `:status()` value, `:status("complete")` included.
- **An unchanged named-paths reload writes a ledger entry** (#455), with `"status": "unchanged"` and a `version_uuid`.
- **The root ledgers are always written** (#452), whatever `[listeners] groups` says. If you had left `default` out, you will now get ledgers.
- **Every new ledger entry has a lifecycle** (#458, #529): `active` on write, `deleted` when the entity is deleted. Ledger reads keep deleted entries, marked, so use `:lifecycle("active")` to leave them out. Entries written before this release have no lifecycle value, so they do not match `:lifecycle("active")`.
- **`ResultMetadata.named_paths_uuid` is always the named-paths group uuid** (#445). The group run uuid moved to `ResultMetadata.group_run_uuid`. OpenLineage v1 result events now always name the group run as their parent (start events already did; completion events named the group). This matters to listener authors.

## Changes in behaviour

Each change has an example.

### Reads that now return records, not bytes

```
$*.files.:manifest()           before: the ledger file's bytes    now: the ledger's records (a list of dicts)
$*.csvpaths.:manifest()        before: bytes                      now: records
$alpha.files.:manifest()       before: bytes                      now: the named-file's manifest records
$acme.csvpaths.:definition()   before: bytes                      now: the definition as a JSON object
```

A framework JSON file (a manifest, a definition or a ledger) resolves to its JSON structure. File content still resolves to bytes: version files, run data files, `README.md` and `:file(...)`. If your code called `json.loads()` on these results, it now gets the structure directly.

### Reference expressions

- **A paths side carries only paths and uuids.** `$orders.files.:all() SUBTRACT $orders.files.:first()` used to read every version's bytes into `.data`. Now `.data` is `None` and no content is read.
- **An argued field is a filter, not a value.** `$a.files.:all().:last() INTERSECT $a.files.:all().:type("csv")` used to raise ("cannot compare a 'paths' left side ... against a 'values' right side"). It now keeps the left side's versions that are csv versions.
- **Whole-file JSON sides cannot be join keys.** `$alpha.files.:definition() INTERSECT $beta.files.:definition()` now raises "cannot use a dict ... as a join key". It used to compare raw bytes, which was sensitive to whitespace. The `$*` ledger sides behave the same way ("cannot use a list").
- **A values side and an argued side do not union.** `$*.results.:flatten():run_uuid() UNION $*.results.:flatten():run_uuid("a1")` now raises: the argued right side is a filter, so it is a paths side.
- **New: parsing from a string.** `ReferenceExpression3.from_string(expression=..., csvpaths=...)` parses a written expression; text with no operator raises "Not a reference expression". Groups nest with parentheses, and operators are case-insensitive (`UNION`, `union`). Two operators without parentheses raise, because there is no precedence yet: `A UNION B SUBTRACT C` raises, while `(A UNION B) SUBTRACT C` works. The CLI uses it, so `:regex("x UNION y")` no longer splits a reference in two.
- **Operator words are reserved at the expression level.** A segment named `union` written after a space (`$acme.files. union`) is read as an operator, and the expression then fails loudly. `$acme.files.union`, with no space, is unaffected.

### RESULTS: a run name pattern followed by a filter

```
$x.results.:regex(/2026-10/):completed(:false())     before: []    now: October's runs that did not complete
$x.results.:regex(/2026-10/):last()                  before: []    now: [] (unchanged: a pointer makes the pattern a template level)
```

A trailing pattern names runs when only filters follow it (field accessors, `:having()`). A pointer, range, grouping function or time window after it makes the pattern a template level. A pattern that matches a template directory and is followed by filters reads as that template level, as its literal spelling does.

### One version file per resolve

```
$orders.files.:name("orders.csv").:all()     before: four files' bytes in one resolve    now: query() lists the four; resolve() raises "more than one version file"
```

Only one file's content can be read per resolve (compendium 5.3). Use a pointer (`:last()`, `:index(n)`), or `resolve_from()` with one of `query()`'s results (#639). Several manifest entries, being records, still resolve together (#632).

### RESULTS: name_one must name a run

`$acme.results.beta` (a template directory, not a run) now raises "names no run". Write `$acme.results.beta/*` for the runs under it, or a run dir name, a pointer or a range. A clock value as the last segment (`customers/:year()`) must name a run too.

### Field accessors take a filtering argument

Twenty-nine scalar field accessors now filter, as the compendium says (6.40): `$acme.results.:last().*:identity("orders")`, `:completed(:false())`, `$alpha.files.:manifest():file_name("one.csv")`. `:instance_index()` reads as a number: bare `:instance_index()` resolves to `1`, not `"1"`. The time fields (`:time()`, `:time_completed()`, `:named_file_last_change()`) and six definition-sourced fields still take no argument; use a date window or a range for time.

- Collection fields take only `:has_value()` / `:does_not_have_value()`, e.g. `$*.csvpaths.:destinations(:has_value())`. An equality test on a list or a dict raises. FILES `:sources()` takes no argument yet.
- Key-selecting fields keep their argument as part of the name: `:source_port("email")` reads `sources.email.port`. This is the one exception to "an argument filters".

### `:files_complete()` is disabled

It is no longer a registered function, so it raises "Unknown reference function" and no longer appears in function listings. The manifest flags behind it are not reliable yet.

### Results that change without an error

These give a different answer, quietly, so check any reference that relies on them:
- **Instances in the RESULTS ledger set count in declaration order** (#643): `$*.results.:manifest():last().:first()`, `:index(0)` and `:all()` follow the statement order in the group, not arrival. An `s1` that arrived before `s0` used to come first.
- **A FILES ledger record is named by its live manifest's owner** (#662): after a rename, `$*.files.:manifest():named_file_name("orders-renamed")` finds the records; the old ledger name no longer does.
- **A CSVPATHS version is named by its owning group** (#663): `$:choice("acme-renamed").csvpaths.:manifest():first()` changes in the same way.
- **Reloading named-paths without `append`** (#719) now deletes the earlier source copies (`*.yml`, `*.yaml`, `*.macie.json`), their reports and stale Macie allow lists.
- **A pointer or range under `*` gives one result per group** (#518, #547), as `$name` would for each name:
  - `$*.results.:last()` gave `w1`; it now gives `a2, w1`;
  - `$*.results.:from(0):to(1)` gave `a0, a1`; it now gives `a0, a1, w0, w1`;
  - FILES groups by named-file: `$*.files.*.:last()` gave `two-2` and now gives `one-2, two-2`, and `$*.files.:last()`, which raised, gives one result per named-file;
  - `:flatten()`, `:manifest()`, `:all()` and `:groups()` still pool across groups, so use them for one pooled answer.
- **Bare `$*` field reads see only live versions** (#494); only `:manifest()` reaches the whole ledger:
  - `$*.csvpaths.:uuid()`, `:fingerprint()` and `:named_paths_name()` no longer include deleted versions or unchanged reloads;
  - `$*.files.:status("failed")` and `$orders.files.:status("failed")` are always `[]`, because a failed registration is never a live version. Use `$*.files.:manifest():status("failed")`.
- **A `:date()` upper bound is that day's first moment** (#587): `:to(:date("2026-01-31"))` no longer includes the 31st. The same goes for directional anchors such as `:yesterday()`.
- **A comparison on a missing value never matches** (#611): `:above()`/`:below()` on a field with no value used to raise a bare `TypeError`; the record is now left out, with a warning.

### New

- A trailing `*` is legal (#646): `$alpha.files.*` is every file directly under alpha, and `$acme.results.beta/*` every run under the `beta` template.
- A RESULTS run dir can be named directly (#644): `$acme.results.beta/2026-01-01_00-00-00`.
- `:having()` filters by content (#641): `$acme.results.:having(:errors(:idchain("add[0]")))` is the runs with that error.
- `:definition()` takes a field chain (#501), and a bare definition field is a one-field chain (#506).
- An argued `:uuid()` or `:fingerprint()` next to a pointer is a filter (#542); it used to raise. `$acme.csvpaths.:last():uuid("a1")` is a1 even when a1 is not the last version.
- A "check SQL coverage" item in the CLI's references menu (#471).

### Ordering is deterministic

Functions in a chain are order-independent: a range applies first, then every filter, then the pointer (compendium 6.28). So `:completed(:false()):last()` and `:last():completed(:false())` mean the same.

## Errors that are now loud

- A ledger entry with no `uuid` raises (logged) when the ledger is read, in every datatype. One bad entry in a ledger makes every read of that ledger raise.
- A JSON file the references read (`errors.json`, `meta.json`, `vars.json`, a manifest, a definition) that does not parse raises a `ReferenceException3` naming the file.
- A corrupt root ledger read by the managers (`inputs/named_files/manifest.json`, `inputs/named_paths/manifest.json`, `archive/manifest.json`) raises a `ValueError` naming the file and the likely cause, e.g. "ends partway through an entry: a write was probably interrupted". It used to be a bare `JSONDecodeError`.
- An undotted field chain on name_one (`$acme.files.:name("orders.csv"):fingerprint()`) already raised; the message now gives the dot form, `$acme.files.:name("orders.csv").:fingerprint()` (#500).
- A name_three after a bare FILES `:manifest()` (`$:regex(/^al/).files.:manifest().:all()`) already raised. Its message now names the chain form, `:manifest():last()` (#711). In CSVPATHS a name_three there picks a statement, as before.

## Fixes outside the reference language

- Results reads no longer write a missing manifest. A results read could write `{}` to a manifest a run was still writing, and so corrupt it (#609; #709 and #722).
- Template clock tokens (`:year`, `:month_name` and the rest) follow DateUtility's date offsets (#437).
- OpenLineage v1 builds file locations from the path itself, not the working directory (#225). `Metadata.base_path` is kept for this release; nothing in the framework reads it now.
- The results metadata keeps `named_file_size` and `named_file_last_change` when a run's metadata is rebuilt.

## Things to know

- **Secrets in definitions.** A malformed `definition.json` that holds a plaintext secret (e.g. a misspelt `passwrd`, or a numeric password) can echo the value into a validation error message, and from there into logs. Keep secrets in environment variables, not in definitions.
- **Name case sensitivity depends on where names are read from.**
  - With `[references] sql = off`, a lookup that touches the filesystem (a literal name) follows it: Windows and macOS (by default) ignore case, and Linux does not. Cloud backends have not been checked yet. Ledger-based reads (`$*`, `:regex()`, `:choice()`) compare names as strings, so they are case-sensitive.
  - With `on`, names come from the database: MySQL's default collation ignores case, and SQLite and Postgres do not.
  - So one reference can give different answers in the two modes on one machine. Treat names as case-sensitive, and never register names that differ only in case.
- **The SQL setting, `[references] sql`** (new; #447, #459, #462, #465):
  - `off`, the default and blank: references read the filesystem, the source of truth.
  - `on`: references read FILES, CSVPATHS and RESULTS metadata from SQL.
  - `shadow`: every read goes to both, the two are compared, any difference is logged, and the filesystem result is returned. A SQL read that raises is logged and re-raised; it does not fall back. It is for proving a SQL setup in dev and test; it reads twice, so it is not a production setting.
  - Anything else raises a `ConfigurationException`.
  - Under `on` and `shadow`, a startup check runs before the first reference read. It raises if `[sql]` dialect or connection string is unset, if one of the four SQL listeners is not configured, or if the database cannot be reached.
  - SQL listener failures used to be logged and swallowed. Under `on` a failed write now always raises `RequiredListenerException`; under `off` and `shadow` it follows the CsvPaths error policy, so with a `raise` policy it now raises.
  - The SQL listeners store exactly the manifest entry each registrar wrote (#445).

## Coming after this release

Tracked as issues:
- atomic manifest writes (#707);
- readers that skip runs still in progress (#708);
- a name_three selector after a bare `:manifest()` (#710);
- a key selector plus generic accessors in place of the key-selecting fields (#721).
