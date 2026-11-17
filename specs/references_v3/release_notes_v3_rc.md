# References v3: release notes for the release candidate

Draft, 2026-11-16, for David to edit. It covers the references language (`$name.datatype.name_one.name_three`) and reference expressions. CVL matching-function changes are covered separately.

## Changes in behaviour

Each change has an example. "Before" is the last release.

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
- **An argued field is a filter, not a value.** `$a.files.:all().:last() INTERSECT $a.files.:all().:type("csv")` used to raise ("cannot compare a 'paths' left side ... against a 'values' right side"). It now keeps the csv versions.
- **Whole-file JSON sides cannot be join keys.** `$alpha.files.:definition() INTERSECT $beta.files.:definition()` now raises "cannot use a dict ... as a join key". It used to compare raw bytes, which was sensitive to whitespace. The `$*` ledger sides behave the same way.
- **A values side and an argued side do not union.** `$*.results.:flatten():run_uuid() UNION $*.results.:flatten():run_uuid("a1")` now raises: the argued right side is a filter, so it is a paths side.
- **New: parsing from a string.** `ReferenceExpression3.from_string(expression=..., csvpaths=...)` parses a written expression. Groups nest with parentheses, and operators are case-insensitive (`UNION`, `union`). Two operators without parentheses raise, because there is no precedence yet: `A UNION B SUBTRACT C` raises, while `(A UNION B) SUBTRACT C` works. The CLI uses it, so `:regex("x UNION y")` no longer splits a reference in two.
- **Operator words are reserved at the expression level.** A segment named `union` written after a space (`$acme.files. union`) is read as an operator.

### RESULTS: a run name pattern followed by a filter

```
$x.results.:regex(/2026-10/):completed(:false())     before: []    now: October's runs that did not complete
$x.results.:regex(/2026-10/):last()                  before: []    now: [] (unchanged: a pointer makes the pattern a template level)
```

A trailing pattern names runs when only filters follow it (field accessors, `:having()`). A pointer, range, grouping function or time window after it makes the pattern a template level. A pattern that matches a template directory and is followed by filters reads as that template level, as its literal spelling does.

### RESULTS: name_one must name a run

`$acme.results.beta` (a template directory, not a run) now raises "names no run". Write `$acme.results.beta/*` for the runs under it, or a run dir name, a pointer or a range. A clock value as the last segment (`customers/:year()`) must name a run too.

### Field accessors take a filtering argument

Most scalar field accessors now filter, as the compendium says (6.40): `$acme.results.:last().*:identity("orders")`, `:completed(:false())`, `$alpha.files.:manifest():file_name("one.csv")`. `:instance_index()` reads as a number: bare `:instance_index()` resolves to `1`, not `"1"`.

- Collection fields take only `:has_value()` / `:does_not_have_value()`, e.g. `$*.csvpaths.:destinations(:has_value())`. An equality test on a list or a dict raises. FILES `:sources()` takes no argument yet.
- Key-selecting fields keep their argument as part of the name: `:source_port("email")` reads `sources.email.port`. This is the one exception to "an argument filters".

### `:files_complete()` is disabled

It is no longer a registered function, so it raises "Unknown reference function" and no longer appears in function listings. The manifest flags behind it are not reliable yet.

### Ordering is deterministic

Functions in a chain are order-independent: a range applies first, then every filter, then the pointer (compendium 6.28). So `:completed(:false()):last()` and `:last():completed(:false())` mean the same.

## Errors that are now loud

- A ledger entry with no `uuid` raises (logged) when the ledger is read, in every datatype. One bad entry in a ledger makes every read of that ledger raise.
- A JSON file the references read (`errors.json`, `meta.json`, `vars.json`, a manifest, a definition) that does not parse raises a `ReferenceException3` naming the file.
- A corrupt root ledger read by the managers (`inputs/named_files/manifest.json`, `inputs/named_paths/manifest.json`, `archive/manifest.json`) raises a `ValueError` naming the file and the likely cause, e.g. "ends partway through an entry: a write was probably interrupted". It used to be a bare `JSONDecodeError`.
- A name_three after a bare FILES `:manifest()` (`$:regex(/^al/).files.:manifest().:all()`) raises a clear error pointing to the chain form, `:manifest():last()`.
- Several version files cannot be resolved in one call (compendium 5.3). Use a pointer, or `resolve_from()` with one of `query()`'s results.

## Fixes outside the reference language

- Reading results never writes. A results read could write `{}` to a manifest a run was still writing, and so corrupt it (#609).
- Template clock tokens (`:year`, `:month_name` and the rest) follow DateUtility's date offsets (#437).
- OpenLineage v1 builds file locations from the path itself, not the working directory (#225). `Metadata.base_path` is kept for this release and will be removed later.
- The results metadata keeps `named_file_size` and `named_file_last_change` when a run's metadata is rebuilt.

## Things to know

- **Ledger reads include deleted entries, marked.** A ledger is the history. Use `:lifecycle("active")` to leave deleted entries out.
- **Entries written before this release's lifecycle change** carry no `"active"` value, so they do not match `:lifecycle("active")`.
- **Secrets in definitions.** A malformed `definition.json` that holds a plaintext secret (e.g. a misspelt `passwrd`, or a numeric password) can echo the value into a validation error message, and from there into logs. Keep secrets in environment variables, not in definitions.
- **Name case sensitivity depends on where names are read from.**
  - With `[references] sql = off`, names come from the filesystem: Windows and macOS (by default) ignore case, and Linux does not.
  - With `on`, names come from the database: MySQL's default collation ignores case, and SQLite and Postgres do not.
  - So one reference can give different answers in the two modes on one machine. Treat names as case-sensitive, and never register names that differ only in case.
- **The SQL setting.**
  - `[references] sql` is `off` by default (the filesystem is the source of truth); the other values are `on` and `shadow`, and anything else raises a `ConfigurationException`.
  - Under `on`, a failed SQL listener write always raises `RequiredListenerException`.
  - Under `off` and `shadow`, it follows the CsvPaths error policy (#447).
  - The SQL listeners store the registrar's manifest entry (#445).

## Coming after this release

Tracked as issues:
- atomic manifest writes (#707);
- readers that skip runs still in progress (#708);
- a name_three selector after a bare `:manifest()` (#710);
- a key selector plus generic accessors in place of the key-selecting fields (#721).
