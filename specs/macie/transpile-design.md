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
  macie_allow_words.nocontrib("<allow list name>", load_list("<allow list id>"))
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
  (#470, #499) instead: see "Text allow lists" below.
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

- **Translated:** custom data identifiers (`macie_cdi`), managed
  identifiers we have a stand-in for (`macie_mdi`), regex allow lists
  (`macie_allow_regex`), and readable text allow lists
  (`macie_allow_words`, with `load_list()`).
- **Reported, not translated:** managed identifiers without a stand-in,
  text allow lists that could not be read at download time, findings
  filters (they act on findings after detection), and every wrapper
  warning.
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
  (loading into a named-paths group, later) will supply them from the rulesbase
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
| `ManagedCatalog` | our managed identifier stand-ins, from `csvpath/macie/rulesbase/managed_identifiers.json`, checked on load |
| `ManagedIdentifier` | occurrences of one managed identifier in one cell: detector, keyword mode, allow lists |
| `CreditCardDetector` | 13-19 digits (or grouped), Luhn, issuer prefix and length, less issuer test numbers |
| `GroupedDigitsDetector` | fixed-length digits, printed in groups or fixed formats, with a named check digit: SIN, NHS, CPF, CNPJ, SUBE |
| `ClRutDetector` | Chile RUT and RUN: 7 or 8 digits and a check character, 0-9 or K |
| `VinDetector` | 17-character VINs; no check digit required |
| `BankAccountDetector` | FR, DE, IT, ES, UK: IBANs (no keyword) and BBANs (keyword), plus UK sort code and account |
| `IbanDetector` | one country's IBANs: length, printed layout, ISO 13616 mod 97 |
| `UsSsnDetector`, `UsNpiDetector` | SSA's SSN rules; CMS's NPI check digit (Luhn over 80840) |
| `ChecksumUtility` (`chut`) | check-digit algorithms (Luhn so far) |
| `MacieMdi` (`macie_mdi`) | applies a managed identifier to every cell |
| `MacieRun` | one run's shared state (allow lists, tally) and outputs; limits from metadata, config, defaults; noisy setup failure |
| `MacieAllowRegex` (`macie_allow_regex`) | registers a regex allow list before any line is read |
| `MacieAllowWords` (`macie_allow_words`) | registers a text allow list, from `load_list()`, before any line is read |
| `MacieGroupLoader` | the Macie side of a group load: convert a wrapper file, store its text lists, refuse shared ids and conflicting lists |
| `MacieCdi` (`macie_cdi`) | applies a custom identifier to every cell; matches lines with an occurrence |
| `MacieReport` (`macie_report`) | summary and `macie_findings`, once |

The CVL functions are listed in
`csvpath/matching/functions/internal.imports` and imported on first use.
`tests/macie/test_macie_functions.py` covers them one behavior at a time;
`tests/macie/test_macie_normative_runs.py` runs each pair's expected
csvpath through real CVL.

`tests/macie/test_macie_pair_semantics.py` runs every normative pair's
data through these classes, without CVL, and checks the pair's expected
findings, finding lines, errors and printouts.

## Managed data identifiers

Macie publishes each managed identifier's keywords, and some of its rules,
but not its implementation. Ours are **stand-ins**, kept as data in a
packaged catalog, `csvpath/macie/rulesbase/managed_identifiers.json`.
`ManagedCatalog` checks the catalog when it loads.
- **Each entry has:** category, detector, keyword mode, keyword list,
  distance, severity, a fidelity tier, the source page and the date it
  was retrieved.
- **Each detector** has its own data, e.g. the card prefix table and
  the issuer test numbers.

The converter writes one `macie_mdi(...)` for each resolved managed
identifier that has a stand-in. They go after the custom identifiers, in
the wrapper's resolved order. Identifiers with no stand-in are still
reported as not translated. The keywords and the severity are written out
in the csvpath, so they are fixed when the group is loaded, as the limits
are. The detector's data is looked up by detector name when the csvpath
runs. (David, 2026-11-01: a middle path between writing everything out
and referencing everything; more indirection can come later if it helps.)

```
macie_mdi(
    "CREDIT_CARD_NUMBER",
    "FINANCIAL_INFORMATION",
    "credit_card",
    "required",
    "account number|american express|amex|...|visa",
    30,
    "1:HIGH"
)
```

**Keyword modes:**
- `required`: a keyword must be in the column name, or near the
  occurrence in the cell.
- `absent`: reported only when there is no keyword there. Macie's
  `CREDIT_CARD_NUMBER_(NO_KEYWORD)` reports card numbers that *aren't* near
  a keyword, so with both selected each card is counted once.
- `none`: keywords are not considered.

**"Near" for managed identifiers** differs from custom identifiers. Macie
says a keyword must be "in proximity", "typically within 30 characters
(inclusively)". For CSV it must be "part of the same value or in the name
of the column". We take that as: in the same cell, **before or after** the
occurrence, with at most 30 characters between them.

**Severity** follows Macie's published table for the identifier's type.
Credit card numbers are HIGH from one occurrence, with or without a
keyword (`1:HIGH`).

**Credit cards** (`CREDIT_CARD_NUMBER`, `CREDIT_CARD_NUMBER_(NO_KEYWORD)`):
- a 13-19 digit sequence that passes Luhn;
- a brand prefix and length from our table, for American Express,
  Dankort, Diners Club, Discover, Electron, JCB, Mastercard, UnionPay and
  Visa (Macie does not publish its table);
- not one of the 55 issuer test numbers Macie lists;
- not touching other digits.

**Ours, not Macie's:** grouped numbers with spaces or hyphens are also
accepted, using one separator throughout, in the common layouts (4-4-4-4,
4-4-4-4-3, Amex 4-6-5, Diners 4-6-4). Macie only documents digit
sequences; we would rather over-detect than miss. This may be a place
users want to customize toward Macie (David, 2026-11-01).

**US Social Security numbers** (`USA_SOCIAL_SECURITY_NUMBER`) and
**National Provider Identifiers** (`USA_NATIONAL_PROVIDER_IDENTIFIER`):
Macie publishes only their keywords, so the formats come from the issuing
standards.
- **SSN:** AAA-GG-SSSS with hyphens, spaces (one separator throughout) or
  no separator. It must not be one SSA never issues: area 000, 666 or
  900-999, group 00, serial 0000. Three widely published example numbers
  are excluded (ours).
- **NPI:** 10 digits starting with 1 or 2, where the check digit is the
  Luhn check digit over `80840` followed by the first nine digits (CMS).
  No separators.
- Both require a keyword, are PERSONAL_INFORMATION, and are HIGH from one
  occurrence.

**IBANs**: Macie's 52 `<COUNTRY>_BANK_ACCOUNT_NUMBER` identifiers.
- **One detector with a parameter.** `iban` takes the ISO 3166 country
  code, written `"iban:GB"` in the catalog and in the csvpath, so each
  identifier stays one readable `macie_mdi(...)`. A detector declares
  `TAKES_PARAMETER`. A detector that takes a parameter must be given one,
  and one that doesn't must not be; either mistake fails.
- **Detection.** Macie: up to 34 alphanumeric characters, ISO 13616, with
  no separator or with space or hyphen separators, validated by Modulus
  97 (`chut.iban_mod97`), and no keyword. Ours:
  - the country's IBAN length, from the SWIFT IBAN registry, which Macie
    does not publish;
  - separators only in the printed layout of groups of four, one
    separator throughout;
  - letters in either case.
- **Severity.** FINANCIAL_INFORMATION, HIGH from one occurrence.
- **BBANs.** Macie's France, Germany, Italy, Spain and UK identifiers
  also detect national Basic Bank Account Numbers near a keyword, and the
  UK one also detects domestic sort code and account numbers
  (`60-16-13 31926819`). Those five use the `bank` detector (`bank:GB`,
  ...): IBANs as above, which need no keyword, plus the country's BBAN,
  which needs one from Macie's per-country list. The detector marks IBAN
  matches `keyword_exempt`, and `ManagedIdentifier` skips the keyword
  rule for exempt matches when the mode is `required`. A BBAN inside an
  IBAN is part of the IBAN, not a second account.

  | Country | BBAN shape | Printed layouts | Check |
  |---|---|---|---|
  | France | 10 digits, 11 letters or digits, 2 digits | groups of 4; 5-5-11-2 | RIB key (`chut.fr_rib_key`) |
  | Spain | 20 digits | groups of 4; 4-4-2-10 | two check digits (`chut.es_bban`) |
  | Italy | letter, 10 digits, 12 letters or digits | groups of 4; 1-5-5-12 | none: the CIN letter is not checked |
  | Germany | 18 digits | groups of 4; 8-10 | none |
  | UK | 4 letters, 14 digits; plus sort code and account | groups of 4; 4-6-8; `##-##-## ########` and `## ## ## ########` | none |

  The French RIB key and the Spanish check digits were confirmed against
  the BBANs inside published IBANs that pass mod 97. Italy's CIN rule
  could not be confirmed from an authoritative source, and a wrong rule
  would miss real accounts, so it is not enforced. Germany and the UK
  have no generic BBAN check, because account checks there are
  bank-specific. The layouts are ours.

**Canada SIN, UK NHS numbers and VINs**:
- **`CANADA_SOCIAL_INSURANCE_NUMBER`** and **`UK_NHS_NUMBER`.** Macie
  publishes only their keywords. Both are "grouped digits with a check
  digit", so one class, `GroupedDigitsDetector`, serves two detector
  names, each with its own catalog data:
  - SIN: 9 digits, Luhn, printed 3-3-3, never starting with 0 or 8. The
    Government of Canada example number is excluded.
  - NHS: 10 digits, mod 11 (`chut.nhs_mod11`: weights 10 down to 2; a
    check of 10 is never issued), printed 3-3-4.
  - Both are HIGH from one occurrence.
- **`VEHICLE_IDENTIFICATION_NUMBER`.** Macie: 17 characters, ISO 3779 and
  3780, "designed for worldwide use". Ours:
  - the VIN alphabet (no I, O or Q);
  - a model-year character in position 10 (not U, Z or 0);
  - letters and digits mixed.

  The North American check digit is **not** required, because VINs from
  elsewhere don't have one, so the fidelity tier is B. Severity is LOW,
  then MEDIUM from 100 occurrences, per Macie.
- All three are PERSONAL_INFORMATION and require a keyword.

**Brazil CPF and CNPJ, Chile RUT and Argentina SUBE**: all four are
PERSONAL_INFORMATION and require a keyword.
- **`BRAZIL_CPF_NUMBER`** and **`BRAZIL_CNPJ_NUMBER`.** Macie publishes
  only their keywords, as one shared Brazil list, so a `cpf` or `cnpj`
  header serves both. The formats are Receita Federal's:
  - CPF: 11 digits, printed `###.###.###-##` or contiguous, two mod 11
    check digits (`chut.cpf_mod11`).
  - CNPJ: 14 digits, printed `##.###.###/####-##` or contiguous
    (`chut.cnpj_mod11`).
  - For both, one digit repeated (e.g. 111.111.111-11) passes the check
    but is never issued, so it is rejected.
  - Both are HIGH. Brazil issues alphanumeric CNPJs from July 2026; ours
    are numeric only, so the converter reports CNPJ as partially
    translated.
- **`CHILE_RUT_NUMBER`.** Macie says it detects RUN and RUT numbers, and
  never reports numbers whose digits are all zeroes. The format is ours:
  a 7 or 8 digit body, optional thousands dots, an optional hyphen, and
  a check character 0-9 or K (`chut.rut_check`, mod 11). HIGH.
- **`ARGENTINA_TARJETA_SUBE`.** Macie documents it fully: 16 digits
  starting 6061, Luhn, with spaces, hyphens or no separator. MEDIUM, then
  HIGH from 100.

`GroupedDigitsDetector` gained printed `formats` with fixed separators
(`#` for a digit), `prefixes` and `reject_repeated`, so CPF, CNPJ and
SUBE are catalog data on the same class as SIN and NHS.

Each managed identifier is a catalog entry plus a detector in
`csvpath/macie/detectors/`, named in `DETECTORS`. One class may serve
several detector names. A test checks that
every detector the catalog names exists, and every detector is used.

**Interpretations to confirm** in the fidelity scan:
1. In-cell keywords count before or after the occurrence, within 30
   characters of the gap.
2. Grouped card numbers: does Macie detect them? Its docs explicitly
   allow spaces and hyphens for the Argentina SUBE card ("can be
   separated by spaces or hyphens") but say only "digit sequence" for
   credit cards, which suggests Macie may not.
3. Keywords match as substrings, as for custom identifiers, so the short
   ones (`mc`, `pan`, `card`) match inside longer words, e.g. a header
   `discard_reason`. That over-reports keyword presence. A value must
   still pass Luhn and the prefix table.
4. Macie "in certain cases" expands or abbreviates keywords. It does not
   say how, so we don't.
5. SSN and NPI formats are the issuers' rules, not Macie's (which are not
   published), e.g. whether Macie accepts SSNs with spaces or none.
6. IBANs: does Macie accept separators anywhere, or only in groups of
   four as we do? Does it accept lower case?
7. VINs: does Macie require the North American check digit for
   North American VINs? We never require it. SIN and NHS formats and
   layouts are the issuers', as for SSN and NPI.
8. CPF, CNPJ and RUT formats are the issuers'. Does Macie accept a RUT
   with no hyphen (`123456785`), as we do? Does it reject repeated-digit
   CPFs and CNPJs?
9. BBANs: does Macie check Italy's CIN letter, or anything for German
   and UK BBANs? Which printed layouts does it accept? (Macie's examples
   are only contiguous and groups of four.)

**Customizing the stand-ins**, via a project `rulesbase` copied in on load
and never overwritten, with a hierarchy and `common.json`, is a later
worklist item. For now the converter takes a `catalog=` argument.

## Loading into a named-paths group

`PathsManager.add_named_paths_from_file()` loads a `.macie.json` wrapper as
a named-paths group, as it loads ODCS contracts:

- `MacieGroupLoader.convert_file()` does the Macie part: load, convert
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

## Text allow lists

A text allow list's entries are in the wrapper (`contents.entries`,
downloaded from S3). There can be 100,000 of them, so they are not written
into the csvpath. The csvpath loads them by the allow list's Macie id:

```
macie_allow_words.nocontrib("contractors", load_list("c0n7r4a1c7o9r5s3a6l0lw"))
```

- **The id, not the name, is the list name.** Ids are short, stable and
  safe as file names; names may hold characters a list name can't.
  `PathsAssetManager.check_list_name()` checks it, and the conversion
  fails if it can't be a list name.
- **In a group, the list is `assets/<id>.txt`.** The load order is:
  convert, refuse a shared csvpath id, refuse a conflicting list (below),
  `configure_named_paths()` if the group is new, `store_list()` for each
  list, then load the csvpath. Both refusals come before anything is
  written. `load_list()` reads the list once, when the csvpath is
  validated; a missing list is an error then, and the csvpath is invalid
  (it does not run as if it had no allow list).
- **Stand-alone** (`convert(path=...)`), the caller passes `list_dir` and
  writes `conversion.lists` there; `load_list()` then reads
  `<list_dir>/<id>.txt`. Without `list_dir` the conversion fails.
- **An unreadable list** (status other than `OK` at download) is reported
  as `allowList.s3WordsList.unreadable` and nothing is stored: alert and
  continue, as in David's notes. Its identifiers still run.
- **The report** (`<file>.report.json`) records each stored list's id and
  entry count, not its entries.
- **A conflicting list is refused.** When appending, a list already in the
  group with the same id and different entries is an error: replacing it
  would change what the group's earlier csvpaths allow, and that could
  open a compliance gap. The same entries are fine. Without append the
  group's csvpaths are replaced, so its lists are too. The check is on the
  list file, whoever wrote it. (David, 2026-11-03.)
- Entries are compared and allowed as Macie does: the occurrence text
  equals an entry, ignoring case.

Normative pair `09_text_allow_list` covers it; `tests/csvpaths/test_csvpaths_macie.py`
loads and runs it as a group.

## Decided 2026-10-30 (David)

- One printout (and one error) per occurrence, up to the detail cap.
- `macie_findings` lives in `vars.json`: that is what `vars.json` is for.
- No implicit word boundaries; matched values never printed or stored;
  Macie numbering in findings; inline `|`-separated keywords and ignore
  words; breaker config from rulesbase / config.ini / defaults.
