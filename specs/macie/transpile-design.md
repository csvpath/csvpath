# Macie -> CVL transpile design (draft)

Companion to `wrapper-format.md`. Covers what the generated CVL looks like
and how it behaves. Worked example: the first normative pair,
`tests/macie/test_resources/normative/01_employee_ids/`.

## Decided

- **Column binding: option (b), Macie functions that check every cell.**
  (David, 2026-10-29.) Whole-cell checks in plain CVL (`regex(#col, ...)`)
  can't express Macie's rules, which are defined on each *occurrence*
  (each regex match) inside a cell:
  - keyword before the match within `maximumMatchDistance`, in the same cell
  - ignore words: excluded when the *match* contains one
  - several occurrences in one cell, all counted
  - severity from occurrence counts
  - allow lists, which compare against the occurrence text
  The rule's parameters still appear in the CVL as function arguments, so
  the generated CVL stays readable and editable.
- **One wrapper -> one csvpath -> one named-paths group.** Every identifier
  in the wrapper is checked by the same csvpath. That gives one place to
  hold the shared finding counts the global circuit breaker needs.
- **File suffix `.macie.json`.** See `wrapper-format.md`.

## Generated csvpath shape

```
~
id: <wrapper name>
macie-origin: job
macie-job-id: <job id>
macie-account: <account id>
macie-region: <region>
macie-source-arn: <job or template ARN, with | for each :>
macie-downloaded-at: <ISO 8601 basic format, e.g. 20261029T174000Z>
macie-max-findings: <global breaker>
macie-max-detail: <default per-identifier detail cap>
logic-mode: OR
print-mode: separate
validation-mode: collect, match, no-print, no-raise, no-fail, no-stop
~
$[1*][
  macie_allow_regex.nocontrib("<allow list name>", /<regex>/)
  macie_allow_words.nocontrib("<allow list name>", load_list("<list name>"))
  macie_cdi("<cdi name>", "<cdi ARN or empty>", /<regex>/, "<keywords>", "<ignore words>", <distance>, "<severity levels>")
  macie_mdi("<managed id>")
  last.nocontrib() -> macie_report()
]
```

- **A matched line is a line with at least one finding.** `logic-mode: OR`
  makes any identifier's finding enough to match the line. Clean lines stay
  unmatched, so `collect()` returns the lines with findings.
- **Allow lists come first.** They register shared state for the
  identifiers after them, so they are `.nocontrib` and must precede every
  `macie_cdi`/`macie_mdi`. The transpiler always writes them first.
- **Keywords and ignore words** are passed as one string, entries separated
  by `|`. Only up to 50 keywords and 10 ignore words, so inline is fine.
  The transpiler rejects (fails fast on) an entry that contains `|`.
  Text allow lists, which can have 100,000 entries, use `load_list()`
  (issue #470) instead.
- **Severity levels** are passed as one string, `"1:LOW 5:MEDIUM 10:HIGH"`.
  Absent in the wrapper -> `"1:MEDIUM"`, which is Macie's default.
- **Metadata values must not contain `:`** (the metadata parser treats each
  `:` as a new key). So timestamps use ISO 8601 *basic* format
  (`20261029T174000Z`). The job's or template's ARN is written with `|` in
  place of each `:` (`macie-source-arn: arn|aws|macie2|us-east-1|...`) and
  swapped back by `ArnUtility` (`arut`) at run time. `|` can't occur in a
  Macie ARN, so the swap is unambiguous; it also keeps the partition
  (`aws-us-gov`, `aws-cn`) that rebuilding an ARN from its id would lose.
  Anything reading the raw metadata outside our code sees the `|` form.
  The full wrapper is kept in the group's `_extra_data`. Descriptions are
  left out: they may contain `~` or `:`.
- **Identifier ARNs go in the body, not metadata.** Metadata holds one value
  per csvpath, so each custom identifier's ARN is `macie_cdi`'s second
  argument. Quoted strings in the body keep their colons. A handcrafted
  wrapper with no ARN passes `""`. Both ARNs land in `macie_findings`:
  the identifier's as `arn` (Macie's own field) and the source's as
  `csvpath.source_arn`. A malformed ARN of either kind fails the run.

## Semantics of `macie_cdi`

For each cell of the line, for each non-overlapping regex match, in order:

1. **Keyword check** (skipped when the identifier has no keywords). Passes
   if either:
   - the column header contains a keyword, or
   - a keyword appears earlier in the same cell, and the distance from the
     *end of the keyword* to the *end of the match* is at most
     `maximumMatchDistance`.
   Keywords are case-insensitive. A keyword with spaces also matches with
   the spaces removed, or replaced by `_` or `-` (so `employee id` matches
   the header `employee_id`).
2. **Ignore words.** The match is dropped if the matched text contains an
   ignore word. Case-sensitive.
3. **Allow lists.** The match is dropped if the matched text exactly
   equals a text allow-list entry (case-insensitive), or fully matches an
   allow-list regex.
4. Otherwise it is an **occurrence**: counted, and recorded as a Macie-style
   cell `{column, columnName, row}`.

Regex matching is case-sensitive unless the pattern says `(?i)`, as in
Macie. There are no implicit anchors or word boundaries: `XEMP-223344`
contains a match.

**Interpretations to confirm against real Macie** (in the one-time
fidelity scan):

1. Allow lists compare against the occurrence text, not the whole cell.
   The docs' CSV example only says an entry must not be split across
   cells.
2. The keyword variant rule (space also matching nothing, `_` or `-`) is
   documented for managed identifiers; we apply it to custom identifiers
   too. Pair 1 depends on it (`employee id` vs header `employee_id`).
3. `\d`, `\w`, `\s` are ASCII-only, as in PCRE's default (we compile
   with `re.ASCII`).

## Regex translation

`RegexUtility` (`reut`) rewrites each mid-pattern inline flag, which
Python rejects, into a scoped group with PCRE's scope: to the end of the
enclosing group, carrying into later alternatives of that group.
`ab(?i)cd` -> `ab(?i:cd)`; `a(?i)b|c` -> `a(?i:b)|(?i:c)`. Character
classes and escapes are copied unchanged. Group types other than `(`,
`(?:`, scoped flags and lookarounds raise `MacieException`.

## Row and column numbering

Findings use Macie's numbering, so they can be compared cell by cell with
real Macie findings: `row` is 1-based and the header row is row 1;
`column` is 1-based. So CsvPath line `n` is Macie row `n + 1`. Printouts
give both.

## Output routing

Three destinations, each with one job:

| What | Where | How |
|---|---|---|
| One line per detailed occurrence | `errors.json` | the Macie function hands it to the csvpath's error manager; `validation-mode: collect` keeps it |
| The same line, readable | the `macie` print stream | `print-mode: separate` gives that stream its own printouts file |
| Per-identifier summary | the `macie` print stream | printed by `macie_report()` on the last line |
| All findings, structured | `vars.json` | the `macie_findings` variable |

Why not plain CVL `error()`: it takes only one argument, so it can't name a
print stream, and with `validation-mode: print` the error manager echoes
every error onto the default stream. The Macie functions are Python, so
they call the error manager and print to the `macie` stream directly, and
the generated metadata says `no-print` so nothing is echoed. The cost:
built-in validation errors (rare in generated CVL) are collected and
logged but not printed. (Agreed direction, David, 2026-10-30.)

No config switch between `print()` and `error()`: the detail cap bounds
`errors.json` to at most `max_detail` x number of identifiers entries per
file. (David, 2026-10-30.)

**`match` in validation-mode.** By default the Framework fails any line
that reports an error (`Expression.matches()`), which would unmatch every
line with a detailed occurrence. `match` stops errors from changing a
line's vote, so a line matches exactly when it has a finding. Side effect:
a built-in argument-validation error makes its line match; generated CVL
should never have one.

**Occurrence numbers in detail messages.** The error manager drops an
error identical to an earlier one (same line, source and message), so two
occurrences in one cell would collapse into one. Each detail message
carries the identifier's running occurrence number:
`macie EmployeeId: occurrence 2, line 5 (row 6), column 3 employee_id`.

**Reporting when stopped.** `stop()` ends the run before `last()` gets its
turn, so `macie_report()` never runs after the breaker trips. The function
that trips it prints the summary and stores the findings itself.

**`$[1*]`, not `first_line -> skip()`.** In a header-only file the header
is also the last line, and `skip()` ends that line before `last()` is
reached, so nothing would be reported. Scanning from line 1 gives a
header-only file a final, frozen pass on which `last()` fires (#306).
`macie_report()` overrides the freeze, as `last()` and `fail()` do, and
lifts the variable freeze while it stores the findings.

Printed and stored output never includes the matched value, only its
location (row, column, column name). Macie's findings do the same.

## Findings output

`macie_report()` runs on the last line. It:

- prints one summary line per identifier to the `macie` stream: occurrence
  count, severity, and how many occurrences had detail reported;
- stores the findings in the variable `macie_findings`, so they land in
  the run's `vars.json` with no new file mechanism. The structure follows
  Macie's own `customDataIdentifiers` / `sensitiveData` detections shape:
  exact `count`, plus up to 15 `cells`, the cap Macie itself uses.

Severity is per identifier per file. Below the lowest threshold there is no
finding at all, as in Macie: the identifier is reported with count `n` and
severity `none`.

## Circuit breakers

`print()`/`error()` are expensive per call, so there are two limits.

1. **Detail cap, per identifier: stop reporting, keep counting.** After
   `macie-max-detail` occurrences of one identifier, no more per-occurrence
   printouts for it. Counting goes on (cheap), so count and severity stay
   exact. The summary says "first N shown".
2. **Global breaker: stop the file.** When total occurrences across all
   identifiers reach `macie-max-findings`, the csvpath calls `stop()`. The
   report says it is partial: the line it stopped at, and severities read as
   "at least".

Where the values come from, in priority order:

1. A per-identifier override in the project's `rulesbase` (optional; keyed
   by identifier name or id; for detail cap only).
2. `[macie] max_findings` and `[macie] max_detail` in `config.ini`.
3. Built-in defaults: `max_detail = 15` (matches Macie), `max_findings =
   10000`.

Agreed for now (David, 2026-10-30). Later we may move this kind of config
into the named-paths group's `definition.json`, so the limits travel with
the group instead of the project.

The transpiler writes the values it used into the csvpath's metadata
(`macie-max-findings`, `macie-max-detail`) and per-identifier overrides as
an extra trailing argument, so a run can be traced back to its limits.

Later, not v1: a "stop once every severity is final" mode. Once an
identifier passes its highest threshold, more counting can't change its
severity.

## Summary messages

```
macie EmployeeId: 8 occurrences, severity MEDIUM, detail shown for first 3
macie B: 1 occurrence, severity LOW, detail shown for all 1
macie C: 0 occurrences, severity none (below 1), no detail
macie D: 1 occurrence, severity none (below 3), detail shown for all 1
macie: stopped at line 18450 after 10000 occurrences (max 10000); results are partial and severities are at least as shown
```

## Code so far

The transpiler is `MacieConverter`, named like the ODCS package's
`OdcsConverter`, and it reuses that package's `ConversionReport` and
`CsvPathTextUtility`:

```python
wrapper = MacieWrapperLoader.from_path(path="hr-employee-ids.macie.json")
conversion = MacieConverter(wrapper=wrapper).convert(max_detail=3)
conversion.name             # "hr-employee-ids": the job's name, or name=...
conversion.csvpath          # the csvpath text, root $[1*]
conversion.report.skipped   # what was not translated
```

- **Translated:** custom data identifiers (`macie_cdi`) and regex allow
  lists (`macie_allow_regex`).
- **Reported, not translated:** managed identifiers (not yet), text allow
  lists (need `load_list()`, #470), findings filters (they act on findings
  after detection), and every wrapper warning.
- **Fails the conversion:** a value CVL can't express, such as a
  keyword, ignore word or name with a double quote, or a keyword or ignore
  word with `|`. Skipping part of an identifier would silently change what
  it detects, so we don't. A regex that doesn't translate and compile as
  `macie_cdi()` will compile it also fails, as does a malformed ARN, a
  name that can't be a csvpath id and group name, or a wrapper with no
  custom identifiers.

  This is stricter than the ODCS converter, which reports what it skips,
  and on purpose. A wrong ODCS translation is a data validation error. A
  wrong Macie translation can miss sensitive data, which can become a
  legal problem. So the Macie side fails loudly wherever a silent
  shortfall could change what is detected. (David, 2026-10-31.)
- **Name:** the job's or template's name. A handcrafted wrapper, or a
  Macie name with other characters, needs `name=`. Names are letters,
  digits, `.`, `_` and `-`.
- **Limits:** `max_findings` and `max_detail` are arguments. The caller
  (named-paths registration, later) will supply them from the rulesbase
  and config.ini. The defaults are 10000 and 15.
- **Regex literals** hold the Macie pattern as written, with `/` escaped
  so the literal ends where it should. Grammar characters such as `]`,
  `(` and `,` need no escaping; tests run each through real CVL.

| Class | Job |
|---|---|
| `MacieConverter` | the transpiler: wrapper -> one csvpath, plus a report of what was not translated |
| `MacieWrapperLoader` | load and check a `*.macie.json` |
| `RegexUtility` (`reut`) | Macie regex -> compiled Python regex |
| `KeywordUtility` (`keut`) | keyword variants, header and in-cell checks |
| `SeverityLevels` | thresholds -> severity |
| `AllowListSet` | regex and text allow lists |
| `CustomIdentifier` | occurrences of one custom identifier in one cell |
| `IdentifierTally`, `FindingsTally` | counts, cells, detail cap, breaker, messages, findings |
| `ArnUtility` (`arut`) | checks Macie ARNs; `:` <-> `|` for metadata |
| `MacieRun` | one run's shared state (allow lists, tally) and outputs; limits from metadata, config, defaults; noisy setup failure |
| `MacieAllowRegex` (`macie_allow_regex`) | registers a regex allow list before any line is read |
| `MacieCdi` (`macie_cdi`) | applies a custom identifier to every cell; matches lines with an occurrence |
| `MacieReport` (`macie_report`) | summary and `macie_findings`, once |

The CVL functions are listed in
`csvpath/matching/functions/internal.imports` and imported on first use.
`tests/macie/test_macie_functions.py` covers them one behavior at a time;
`tests/macie/test_macie_normative_runs.py` runs each pair's expected
csvpath through real CVL. Not yet written: `macie_mdi`,
`macie_allow_words`.

`tests/macie/test_macie_pair_semantics.py` runs every normative pair's
data through these classes, without CVL, and checks the pair's expected
findings, finding lines, errors and printouts.

## Named-paths registration

`PathsManager.add_named_paths_from_file()` loads a `.macie.json` wrapper as
a named-paths group, as it loads ODCS contracts:

- `MacieRegistration.convert_file()` does the Macie part: load, convert
  with `[macie] max_findings` / `max_detail` from config.ini (or the
  defaults), name the csvpath, and build the report. The paths manager
  imports the Macie package only when it loads a wrapper.
- The csvpath's id is the job's or template's name, or the wrapper's file
  name when that name can't be an id (e.g. handcrafted wrappers).
- The wrapper is copied byte for byte into the group home, with
  `<file>.report.json` beside it (the same writer as ODCS reports).
- `add_named_paths_from_dir()` loads each wrapper as its own group, named
  for the file without `.macie.json`: a dot in a group name would break
  references to it. Combining a directory into one named group refuses
  wrappers, as it refuses ODCS contracts.
- Only the full `.macie.json` suffix is a wrapper. Other `.json` files keep
  their meaning (group definitions).

**A Macie csvpath's id is unique in its group.** Appending is fine: Macie,
ODCS and plain csvpaths can share a group. But an append that would give a
Macie csvpath's id to a second csvpath is refused before anything is
written. Two csvpaths with one id would scan twice and blur whose findings
are whose. Duplicate ids among non-Macie csvpaths are still allowed: there
they are housekeeping, and teams reuse building-block csvpaths across
groups. (David, 2026-10-31.)

## Decided 2026-10-30 (David)

- One printout (and one error) per occurrence, up to the detail cap.
- `macie_findings` lives in `vars.json`: that is what `vars.json` is for.
- No implicit word boundaries; matched values never printed or stored;
  Macie numbering in findings; inline `|`-separated keywords and ignore
  words; breaker config from rulesbase / config.ini / defaults.
