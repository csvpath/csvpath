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
  The full wrapper is kept in the group home, and each group run copies
  it into the run's `_extra_data/macie/` (rulesbase-design.md, P2b).
  Descriptions are left out: they may contain `~` or `:`.
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
  name that can't be a csvpath id and group name. (A wrapper with only
  managed identifiers is fine; early drafts refused one with no custom
  identifiers.)

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
| `GroupedDigitsDetector` | fixed-length digits, printed in groups or fixed formats, with a named check digit: SIN, NHS, CPF, CNPJ, SUBE, Aadhaar, IdNr, CUIT, TFN, UTR, SPI |
| `EsIdDetector` | Spain DNI, NIE, NIF and CIF: a control letter (mod 23) or a CIF control |
| `MxRfcDetector` | Mexico RFC for people and organizations: letters, a real date, 3 characters |
| `CoNitDetector` | Colombia NIT: body and mod 11 digit; 9 digits from 8 or 9 is an organization's |
| `DateDetector` | birth dates (full, real dates) and card expiration (month and year, and Macie's keyword form) |
| `PhoneDetector` | one country's phone numbers from its numbering plan; a country code makes a number keyword exempt |
| `FormatDetector` | group B: shapes in the catalog's format notation, compiled to one regex |
| `DeIdDetector` | Germany identity card: 9 characters and an ICAO 7-3-1 check digit |
| `MagStripeDetector` | card magnetic stripe tracks 1 and 2, Luhn card number |
| `UsIdDetector` | US DEA (check digit), MBI, ITIN, HICN, NDC and HCPCS |
| `CredentialDetector` | the nine credentials: AWS and Google keys, Basic headers, JWTs, key blocks, PuTTY keys, Stripe keys |
| `FrNirDetector` | France NIR (INSEE): 15 characters, Corsica's 2A and 2B, mod 97 key |
| `MxCurpDetector` | Mexico CURP: 18 characters, birth date, state, check digit |
| `ItCfDetector` | Italy Codice Fiscale: people's 16 characters (omocodia, birth date, check letter) and organizations' 11 digits (office code, Luhn) |
| `ClRutDetector` | Chile RUT and RUN: 7 or 8 digits and a check character, 0-9 or K |
| `VinDetector` | 17-character VINs; no check digit required |
| `BankAccountDetector` | FR, DE, IT, ES, UK: IBANs (no keyword) and BBANs (keyword), plus UK sort code and account |
| `IbanDetector` | one country's IBANs: length, printed layout, ISO 13616 mod 97 |
| `UsSsnDetector`, `UsNpiDetector` | SSA's SSN rules; CMS's NPI check digit (Luhn over 80840) |
| `ChecksumUtility` (`chut`) | check-digit algorithms: Luhn, mod 11s, mod 97, RUT, RIB, Verhoeff, the Spanish mod 23 letter, NIR key, CURP digit, Codice Fiscale letter, IdNr, CUIT, TFN, UTR, CIF, NIT, SPI, DEA, ICAO 9303 |
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

**Spain DNI and NIE, and India Aadhaar**: all three are
PERSONAL_INFORMATION, require a keyword, and are HIGH from one
occurrence (Macie's table for national identification and taxpayer
numbers).
- **`SPAIN_DNI_NUMBER`.** Macie publishes the keywords, and that
  `99999999`, `99.999.999` and all zeroes are never reported. It also
  says it may report an Argentina DNI as a Spain DNI, or the other way
  around. The format is ours, from the Ministerio del Interior: 8 digits,
  optionally dotted, and a control letter, optionally after a hyphen or
  space (`12345678Z`, `12.345.678-Z`). The letter is the number mod 23
  indexing `TRWAGMYFPDXBNJZSQVHLCKE` (`chut.es_id_letter`). We require
  the letter, so a digits-only Argentina DNI is not reported. Macie's
  exclusions (no letter) suggest it may accept digits alone, so the
  fidelity tier is B.
- **`SPAIN_NIE_NUMBER`.** Macie lists it with the taxpayer numbers and
  publishes only Spain's taxpayer keywords, shared with NIF and CIF. The
  format is ours: X, Y or Z, 7 digits and a control letter, the DNI's
  mod 23 with X, Y and Z as 0, 1 and 2 (`X1234567L`, `X-1234567-L`).
  All zeroes are never reported, as Macie says of several taxpayer
  numbers.
- One class, `EsIdDetector`, serves `es_dni` and `es_nie`; the catalog
  data gives the form. Letters may be either case, and numbers must not
  touch other letters or digits.
- **`INDIA_AADHAAR_NUMBER`.** Macie publishes only the keywords. The
  format is UIDAI's: 12 digits, never starting with 0 or 1, the last a
  Verhoeff check digit (`chut.verhoeff`), printed 4-4-4 or contiguous.
  It is catalog data on `GroupedDigitsDetector`. The Verhoeff tables were
  cross-checked against the dihedral group's arithmetic on 20,000 random
  strings; that check caught a mistyped table row before any test ran.

**France NIR, Mexico CURP and Italy Codice Fiscale**: all three are
PERSONAL_INFORMATION, require a keyword, and are HIGH from one
occurrence. Macie publishes only their keywords. Each has its own
detector.

**Germany IdNr, Argentina CUIT and CUIL, Australia TFN and UK UTR**:
taxpayer numbers, all PERSONAL_INFORMATION and keyword required. Macie
publishes only their keywords. All four are `GroupedDigitsDetector` data
with a new named check:
- **`GERMANY_TAX_IDENTIFICATION_NUMBER`**: the Steuer-IdNr, which is
  what Macie says it detects. 11 digits, printed 2-3-3-3, no leading 0;
  in the first ten, exactly one digit occurs two or three times and the
  others once; ISO 7064 MOD 11,10 (`chut.de_idnr`). HIGH.
- **`ARGENTINA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER`** and
  **`ARGENTINA_ORGANIZATION_TAX_IDENTIFICATION_NUMBER`**: CUIT and CUIL,
  11 digits printed 2-8-1, a mod 11 check digit (`chut.ar_cuit`). The two
  share Macie's keywords, so the type prefix decides which reports a
  number: 20, 23, 24 and 27 for individuals; 30, 33 and 34 for
  organizations. The international types 50, 51 and 55 go with
  organizations (ours). Individuals are HIGH; organizations MEDIUM for
  1-99, HIGH from 100, per Macie.
- **`AUSTRALIA_TAX_FILE_NUMBER`**: 9 digits, printed 3-3-3, weighted
  sum divisible by 11 (`chut.au_tfn`). HIGH. **Partial:** older 8 digit
  TFNs are not detected, because the published weights for them
  disagree (python-stdnum's are not Wikipedia's) and a wrong rule would
  miss real numbers.
- **`UK_TAX_IDENTIFICATION_NUMBER`**: Macie says TRNs and UTRs. A UTR is
  10 digits, printed 5-5, the first digit a check over the other nine
  (`chut.gb_utr`). HIGH. **Partial:** TRNs (temporary reference
  numbers) are not detected; their format could not be confirmed.

**Spain NIF and CIF, Mexico RFC, Colombia NIT and France TIN**: more
taxpayer numbers, all PERSONAL_INFORMATION and keyword required. How the
identifiers split was decided with David on 2026-11-03; all but the
French one are fidelity B.
- **`SPAIN_NIF_NUMBER`** and **`SPAIN_TAX_IDENTIFICATION_NUMBER`**:
  Macie says it detects "CIF, NIE, and NIF numbers", with these two and
  `SPAIN_NIE_NUMBER` sharing Spain's taxpayer keywords. NIF is a
  person's NIF: the DNI form, or K, L or M, 7 digits and the DNI's letter
  over the 7 digits. The CIF is `SPAIN_TAX_IDENTIFICATION_NUMBER`: a type
  letter, 7 digits, and a control digit or letter from their Luhn digit
  (`chut.es_cif`; either form is accepted, as sources disagree). NIEs
  stay with `SPAIN_NIE_NUMBER`, so no number is counted twice under the
  shared keywords. More forms of `EsIdDetector`. HIGH.
- **`MEXICO_INDIVIDUAL_RFC_NUMBER`** and
  **`MEXICO_ORGANIZATION_RFC_NUMBER`** (`MxRfcDetector`): 4 letters for
  people, 3 for organizations, then a real YYMMDD date and 3 characters,
  optionally separated by spaces or hyphens. Macie's examples
  `XAXX010101000` and `XEXX010101000` are excluded. **The check digit is
  not checked:** about 1.5% of RFCs in use have a wrong one
  (python-stdnum's note), and a check would miss them. Individuals are
  HIGH; organizations MEDIUM for 1-99, HIGH from 100.
- **`COLOMBIA_INDIVIDUAL_NIT_NUMBER`** and
  **`COLOMBIA_ORGANIZATION_NIT_NUMBER`** (`CoNitDetector`): a body and a
  mod 11 check digit over prime weights (`chut.co_nit`), dotted,
  hyphenated or contiguous. Nothing in a NIT says person or
  organization, so: a 9 digit body starting 8 or 9 is an organization's
  (the usual rule for personas juridicas), any other 6 to 10 digit body
  a person's. A few old cedulas could be counted as organizations; they
  are still reported, at MEDIUM. Individuals are HIGH; organizations
  MEDIUM for 1-99, HIGH from 100.
- **`FRANCE_TAX_IDENTIFICATION_NUMBER`**: the SPI, 13 digits printed
  2-2-3-3-3, the first 0 to 3, the last three the first ten mod 511
  (`chut.fr_spi`). `GroupedDigitsDetector` data. HIGH.
- Keyword overlaps: France's and Spain's lists both have `tin`, `tax
  id` and `tax number`, and Mexico's short `iva` matches inside words
  such as `private` (item 3).

**Credentials**: Macie's nine credential identifiers, category
CREDENTIALS, all HIGH from one occurrence. Only `AWS_CREDENTIALS` and
`GCP_API_KEY` need a keyword. One class, `CredentialDetector`, has a form
for each:
- **`AWS_CREDENTIALS`**: a secret access key, 40 characters of A-Z a-z
  0-9 / +. Macie's two fictitious examples are excluded. Ours: a string
  that is all lower case hex (a SHA-1 hash) is not a key, and neither is
  one part of a dotted token. A JWT whose header is 40 base64 characters
  would otherwise be an AWS key whenever "credentials" is near; the
  normative pair caught it.
- **`GCP_API_KEY`**: the key string, `AIza` and 35 characters.
- **`HTTP_BASIC_AUTH_HEADER`**: a complete `Authorization:` or
  `Proxy-Authorization:` header with the Basic scheme (RFC 7617). The
  field name and scheme may be in any case, and the token is not decoded
  (ours: decoding could only miss real headers).
- **`JSON_WEB_TOKEN`**: three base64url parts; the header decodes to a JSON
  object with `alg` and the payload to a JSON object; the signature may be
  empty (RFC 7519, signed or unsigned).
- **`OPENSSH_PRIVATE_KEY`**, **`PGP_PRIVATE_KEY`** and **`PKCS`**: a whole
  BEGIN ... END block in one cell. PKCS takes `PRIVATE KEY`, `ENCRYPTED
  PRIVATE KEY` and `RSA PRIVATE KEY` blocks; ours, also `EC` and `DSA
  PRIVATE KEY` blocks, the same exposure though not PKCS.
- **`PUTTY_PRIVATE_KEY`**: exactly what Macie describes, the six headers in
  order with the characters Macie allows; so no spaces in values and no
  custom headers.
- **`STRIPE_CREDENTIALS`**: `sk_`, `pk_` or `rk_`, `live_` or `test_`, and
  24 or more letters and digits. Macie's two code examples, a secret and a
  publishable test key, are excluded, which says it reports test and
  publishable keys.
- **Test data:** key blocks, Google keys and Stripe keys are built at run
  time in `test_macie_credentials.py`, so no file in the repo looks like a
  leaked secret to a secret scanner. The normative pair holds only
  harmless shapes. The catalog holds Macie's example keys only as SHA-256
  hashes (`exclusions_sha256`): GitHub push protection blocked a push of
  Stripe's published test key, even as an exclusion.

**US health and taxpayer identifiers**: all PERSONAL_INFORMATION,
keyword required, HIGH from one occurrence. Macie publishes only their
keywords. One class, `UsIdDetector`, has a form for each:
- **`US_DRUG_ENFORCEMENT_AGENCY_NUMBER`**: a registrant type letter, the
  registrant's initial or 9, and 7 digits whose last is a check digit
  (`chut.us_dea`: the 1st, 3rd and 5th digits plus twice the 2nd, 4th and
  6th). Ours: any type letter, so new registrant types are not missed.
- **`USA_MEDICARE_BENEFICIARY_IDENTIFIER`**: CMS's 11 positions (digit,
  letters, letter-or-digit, digits), letters never S L O I B Z, optional
  dashes after the 4th and 7th. CMS's published example `1EG4-TE5-MK73`
  is excluded (ours).
- **`USA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER`**: 9, two digits, the
  middle digits 50-65, 70-88, 90-92 or 94-99 (the IRS ranges since 2011;
  python-stdnum still has only 70-99, so the oracle is not used here),
  four digits.
- **`USA_HEALTH_INSURANCE_CLAIM_NUMBER`**: an SSN by the SSA rules (reusing
  `UsSsnDetector`) and a beneficiary code, a letter and an optional letter
  or digit. **Partial:** Railroad Retirement Board numbers are not
  detected.
- **`USA_NATIONAL_DRUG_CODE`**: 10 digits as 4-4-2, 5-3-2 or 5-4-1, the 11
  digit 5-4-2 billing form, or contiguous. No check digit; fidelity B.
- **`USA_HEALTHCARE_PROCEDURE_CODE`**: HCPCS Level II (a letter A-V and 4
  digits) and, since Macie's keywords include "current procedural
  terminology", CPT codes (5 digits, or 4 and F, T or U). No check
  digit; fidelity B. The keyword does the work: `cpt` alone is not one
  of Macie's keywords.

**Germany identity card, France health insurance number and magnetic
stripe data**: keyword required, HIGH from one occurrence.
- **`GERMANY_NATIONAL_IDENTIFICATION_NUMBER`** (`DeIdDetector`): the
  Personalausweis, 9 characters of 0-9 and the consonants C F G H J K L M
  N P R T V W X Y Z, and an ICAO 9303 check digit (`chut.icao_check`: 7 3
  1 weights, letters 10 to 35). The check was confirmed on the ICAO 9303
  specimen's fields and the official specimen card, T220001293. Some of
  the keywords are broad (`id number`, `insurance number`) and an all
  digit number passes one time in ten, so this can over-report; fidelity
  B.
- **`FRANCE_HEALTH_INSURANCE_NUMBER`**: the health insurance number is the
  NIR, so this reuses `fr_nir` with Macie's health keywords (`carte
  vitale`). The same number near INSEE keywords is the national
  identification number instead; near both, it is both.
- **`CREDIT_CARD_MAGNETIC_STRIPE`** (`MagStripeDetector`), FINANCIAL:
  ISO/IEC 7813 tracks 1 and 2, with or without the sentinels, a card
  number that passes Luhn and an expiry month 01-12.

**Group B: `FormatDetector` and the format notation.** Group B
identifiers have a shape but no check digit, so their shapes are catalog
data (David, 2026-11-05; design in `group-b-design.md`). A detector's
`formats` are written in a small notation: `#` a digit, `A` a letter, `X`
a letter or digit, `[...]` a set of letters, digits and ranges, `{n}` or
`{m,n}` a count, digits and punctuation as themselves. Any other letter
must be in a set (`[L]`), so `AIza` is an error, not a literal. A format
may be an object `{"format": ..., "used_by": [...]}` naming its issuers,
for the US driver's license's state formats. All of a detector's formats
compile when it is created, identical ones once. Where formats overlap,
the longest match at a position is the occurrence, and a piece of a
hyphen-joined token is not one (ours): see driver's licenses.
`exclusions` and `exclude_prefixes` are compared without separators, in
upper case.
- **`UK_NATIONAL_INSURANCE_NUMBER`**: HMRC's rules as sets: two prefix
  letters (D F I Q U V never, O never second), 6 digits, suffix A to D,
  contiguous or `AB 12 34 56 C`; prefixes BG GB KN NK NT TN ZZ excluded.
  The short keyword `nin` matches inside `opening_balance` (item 3).
- **`BANK_ACCOUNT_NUMBER`**: Macie documents it fully, US and Canada,
  9-17 digits with no spaces: `#{9,17}`. FINANCIAL, HIGH.
- **`CREDIT_CARD_SECURITY_CODE`**: `#{3,4}`, so the keyword does nearly
  all the work (fidelity B). MEDIUM for one occurrence, HIGH from two,
  per Macie.

**Passports** (group B step 2): Macie's seven passport identifiers, as
`FormatDetector` formats. PERSONAL_INFORMATION, keyword required, MEDIUM
for one occurrence and HIGH from two (Macie). Fidelity B: the keyword
does most of the work.

| Identifier | Formats | Source |
|---|---|---|
| `CANADA_PASSPORT_NUMBER` | `AA######` | IRCC |
| `FRANCE_PASSPORT_NUMBER` | `##AA#####` | EC document format analysis |
| `GERMANY_PASSPORT_NUMBER` | `[CF-HJK][0-9CF-HJ-NPRTV-Z]{8}` | Auswaertiges Amt (no vowels, no B D Q S); the first letter is ours |
| `ITALY_PASSPORT_NUMBER` | `AA#######` | EC document format analysis |
| `SPAIN_PASSPORT_NUMBER` | `AAA######`, and ours `AA######` (older) | Spanish consulates |
| `UK_PASSPORT_NUMBER` | `#{9}` | HM Passport Office |
| `USA_PASSPORT_NUMBER` | `#{9}`, `A#{8}` (since 2021) | US State Department |

Macie's keyword lists overlap, so one number can be several countries'.
Near the bare keyword `passport` (Canada, Germany, Spain and US lists),
`AB123456` is both Canadian and Spanish; near `passport number` (UK and
US lists, among others), 9 digits are both British and American. We
report what Macie's lists and the shapes imply, and the normative pair
shows it.

**Phone numbers** (group B step 3): Macie's seven phone identifiers
(`PHONE_NUMBER` is the US and Canada), PERSONAL_INFORMATION, LOW for one
occurrence, MEDIUM from 2, HIGH from 100.
- **Macie's rule:** a number near a keyword need not include a country
  code; a number with no keyword near must include one. `PhoneDetector`
  marks a number written with its country code (`+44`, `0044`) keyword
  exempt, through the same `keyword_exempt` hook the bank detector uses
  for IBANs, and the entries are `required`. No new keyword mode was
  needed after all.
- **Numbering plans are catalog data** (David, 2026-11-05, option A):
  `country_code`, `trunk`, `trunk_required` and `nsn_formats` in the
  format notation. The trunk is required in the UK, France and Germany,
  optional in the US (`1`) and Brazil (`0`), and there is none in Italy
  and Spain. An international number may keep the trunk in parentheses,
  `+44 (0)20 7946 0958`.
- **Checked against Google's phonenumbers** (a dev dependency, Apache
  2.0): each country's example fixed line, mobile and toll free numbers
  are found in national, international, E.164 and 00 forms.
- **National numbers can be more than one country's.** Without a country
  code, `0121 234 5678` fits the UK, German, Italian and Brazilian plans,
  and the seven share keywords, so near a keyword it is reported for
  each. International numbers never are. Accepted for the first release
  (David, 2026-11-05): customers can see why in their results, it shows
  only when several countries' phone identifiers are selected, and the
  normative pair shows it. Germany's and Italy's plans are the loosest.
- Ours: two numbers with only a space between read as one and are not
  found.

**Dates** (group B step 4): `DATE_OF_BIRTH` (PERSONAL) and
`CREDIT_CARD_EXPIRATION` (FINANCIAL) on `DateDetector`, keyword required,
LOW for one occurrence, MEDIUM from 2, HIGH from 100 (Macie). Fidelity B.
- **birth**: full dates that are real dates: D/M/Y or M/D/Y (either
  reading), Y-M-D, `5 Nov 1985`, `November 5, 1985`, `1985-Nov-05`, and 8
  digits (YYYYMMDD, DDMMYYYY or MMDDYYYY). One separator throughout.
- **expiry**: `02/26`, `02/2026`, `Feb 2026`, `26-Feb`, and Macie's keyword
  form `expY=2026, expM=02` in either order. A month and year inside a
  full date (`12/25/2026`) is not an expiry date.
- The keyword form carries its keywords inside the occurrence, where
  nearness is not measured, so it is keyword exempt (the same hook).
- Ours: English month names; dots are not separators, as Macie lists
  spaces, slashes and hyphens; a date matching several shapes is one
  occurrence.

**Driver's licenses** (group B step 5): 17 of Macie's 32 driver's license
identifiers, all `FormatDetector` data, PERSONAL_INFORMATION, keyword
required, LOW for one occurrence, MEDIUM from 2, HIGH from 100. Fidelity
B. Scope agreed with David on 2026-11-06: the US, UK, Canada, Australia,
India, Germany, France, Spain, Italy, Austria, Belgium, Bulgaria, Croatia,
Cyprus, Czechia, Denmark and Estonia; the other 15 are on the worklist.
- **Sources:** Macie publishes only keywords. The formats are Microsoft
  Purview's detection patterns (a vendor's, not the issuers'), Skyhigh
  Security's DLP table for the US states, and the DVLA's structure for the
  UK. Each detector's notes say which.
- **The US** is one identifier, as in Macie, so its formats are the union
  of the states' formats, each tagged `used_by` with its states (David,
  2026-11-05). A test checks that all 50 states and DC are covered. Many
  states share a format, so there are 36 formats. Washington's is the
  DOL's `WDL` format since 2018; older Washington numbers are not
  detected (ours).
- **Canada** is likewise a union of the provinces' formats.
- **Ours:** the UK uses the DVLA's 16 characters (with the optional issue
  number), not Microsoft's 18 character description; Germany's check
  digit is not checked (Microsoft does not publish it); Spain's DNI and NIE
  shapes are not letter checked here, as the DNI and NIE identifiers
  check them.
- **Two FormatDetector changes this needed.** Each format is now its own
  regex and the longest match at a position wins: in one regex,
  `A###-####-####` (Illinois) cut `A###-####-####-##` (Wisconsin) short,
  because a hyphen does not stop a match. And a piece of a hyphen-joined
  token is not an occurrence: `56789` in `A1234-56789-07234` is not a 5
  digit Alberta number. Neither changes any earlier normative pair.
- **Overlap:** the English speaking countries share Macie's English
  keywords and many formats are digit runs, so `12345678` near "drivers
  license" is American, Canadian and Australian, the same kind of overlap
  accepted for phones. France's only keyword is French.

**Group B, the rest of the shapes.** Seven more `FormatDetector`
entries. Macie publishes only their keywords (and, for the Argentina DNI,
its exclusions), so every format is ours:
- `ARGENTINA_DNI_NUMBER`: 7 or 8 digits, contiguous or dotted
  (12.345.678). Macie's exclusions, 99999999 and all zeroes, are
  `exclusions` (compared without dots). Macie says it may report an
  Argentine DNI as Spain's and the other way around; ours does not, as
  Spain's DNI needs its check letter.
- `BRAZIL_RG_NUMBER`: states issue RG numbers in their own shapes. We take
  Sao Paulo's, 8 digits and a check character, a digit or X
  (12.345.678-9); the check is not verified, as states compute it
  differently.
- `COLOMBIA_CITIZENSHIP_CARD_NUMBER`: 6 to 10 digits, contiguous or
  dotted between thousands. No check digit.
- `CANADA_NATIONAL_IDENTIFICATION_NUMBER` (Macie's permanent residence
  number): the IRCC client identifier (UCI), 8 or 10 digits, as 1234-5678
  or 12-3456-7890.
- `INDIA_PERMANENT_ACCOUNT_NUMBER`: 5 letters, 4 digits, a letter; the
  fourth letter is the holder type (A B C F G H J L P T). The last letter
  is a check character with no published rule.
- `UK_ELECTORAL_ROLL_NUMBER`: two letters and 1 to 4 digits, Microsoft
  Purview's description.
- `BRAZIL_CEP_CODE`: 8 digits, as 01310-100, 01310100 or 01.310-100.
  Severity is Macie's mailing address row, LOW, MEDIUM from 2, HIGH from
  100.
The short keywords `rg` and `cep` match as substrings (item 3): `org`,
a `cargo` header and `receptor` count. Keywords are matched as Macie
lists them, so `cedula de ciudadania` without its accents is not
Colombia's keyword (item 22).

**Group B, GPS coordinates and HTTP cookies.** Two small detectors, as
the notation cannot check a range or a header's grammar:
- `LATITUDE_LONGITUDE` (`LatLongDetector`): Macie wants a pair in Decimal
  Degrees, e.g. `41.948614,-87.655311`, and an English keyword; not DDM or
  DMS. Ours: both numbers have a decimal part and an optional sign,
  separated by a comma or spaces, the latitude within 90 and the longitude
  within 180. A degree sign after a number makes it DDM or DMS. Severity
  is LOW, then MEDIUM from 2, also from 100 (`1:LOW 2:MEDIUM`).
- `HTTP_COOKIE` (`CookieDetector`): no keyword; a complete `Cookie` or
  `Set-Cookie` header with name=value pairs. Ours, from RFC 6265: the
  field name in any case, a token name and a non-empty value; a
  Set-Cookie header's attributes (`Secure`, `Path=/`) are part of it. One
  header is one occurrence, however many pairs it has.
With these, every group B identifier has a stand-in, except the 15
driver's license countries on the backlog.

**Group A leftovers: `CANADA_HEALTH_NUMBER`** (`CaHealthDetector`).
Macie publishes only the keywords, which point at British Columbia (MSP,
PHN) and Quebec (soins de sante). Our forms are the provinces with a
published structure: British Columbia's PHN, 10 digits starting 9 with a
mod 11 check digit (`chut.ca_bc_phn`, compared with python-stdnum);
Ontario's health number, 10 digits with a Luhn check digit and an optional
version code; Quebec's RAMQ number, 4 letters, a real birth date as
YYMMDD with 50 added to the month for women, and 2 digits. The other
provinces' numbers are digit runs with no published check, which near a
keyword like `phn` would match any number of that length, so they are
missed (item 24). A BC PHN can also pass Luhn; it is one occurrence.

**EHIC and UDI** (David, 2026-11-07: the card ID only, and GS1 + HIBCC
with their checks).
- `EUROPEAN_HEALTH_INSURANCE_CARD_NUMBER` and
  `FINLAND_EUROPEAN_HEALTH_INSURANCE_NUMBER` (`EhicDetector`): Macie
  publishes only keywords, and we found no official EU-wide format. Ours
  is the card's 20 digit identification number, read as an ISO/IEC 7812
  health card number: 80, the issuing country's ISO 3166 numeric code,
  15 digits. Contiguous, two blocks of 10 (Microsoft Purview's Finland
  description) or four of 5. The countries are catalog data: the EU,
  Iceland, Liechtenstein, Norway, Switzerland and the UK for the EU
  identifier; 246 for Finland's. No check digit is verified. The
  personal ID also printed on the card differs by country and is not
  detected (item 25). Macie lists `sairaanhoitokortin` twice for Finland;
  the catalog has it once.
- `MEDICAL_DEVICE_UDI` (`UdiDetector`), human readable forms: GS1, `(01)`
  and a GTIN-14 with its GS1 check digit (`chut.gs1_check`, compared with
  python-stdnum), then optional `(11)` `(17)` dates and `(10)` `(21)` lot
  and serial; HIBCC, `+`, a labeler code, product code and unit of measure
  digit, optional secondary data after `/`, and the mod 43 check character
  over the whole (`chut.hibcc_mod43`, checked against two HIBCC
  specification examples). ISBT 128 is not detected yet. Macie's keywords
  include `med` and `blood`, which match widely as substrings (item 3);
  the check characters keep the false positives down.

**Checks against an oracle.** `tests/macie/test_macie_checksum_oracle.py`
compares every `ChecksumUtility` check that python-stdnum also implements
(Luhn, Verhoeff, CPF, CNPJ, RUT, NHS, mod 97, the Spanish letter, NIR,
CURP, Codice Fiscale, IdNr, CUIT, TFN, UTR, CIF, NIT, SPI) and the
partita IVA rules with stdnum, on seeded
random inputs. python-stdnum is a dev dependency only (LGPL, not
shipped). Reintroducing the mistyped Verhoeff row fails the test.
- **`FRANCE_NATIONAL_IDENTIFICATION_NUMBER`** (`FrNirDetector`, INSEE
  codes): 15 characters, the department 2 digits or Corsica's 2A or 2B,
  and a key of 97 minus the first 13 mod 97, with 2A and 2B as 19 and 18
  (`chut.fr_nir_key`). Printed contiguous, as 1-2-2-2-3-3-2 with spaces
  or dots, or with only the key apart. We apply no rule to the sex digit
  or the month: INSEE uses other values for some people, and a rule we
  can't confirm would miss real numbers. The France list includes the
  bare keyword `social`, which matches widely (item 3).
- **`MEXICO_CURP_NUMBER`** (`MxCurpDetector`): RENAPO's 18 characters, a
  real birth date (the character before the check digit says 1900s or
  2000s), a state code or `NE`, and a check digit over RENAPO's alphabet,
  which has `Ñ` after `N` (`chut.mx_curp_check`). Ours: sex `X` is
  accepted as well as `H` and `M`, so newer CURPs are not missed; RENAPO's
  list of 4 letter words never issued is not applied, since those codes
  never occur.
- **`ITALY_NATIONAL_IDENTIFICATION_NUMBER`** (`ItCfDetector`): Macie lists
  it as both a national identification and a taxpayer number, with one
  keyword list. We detect the 16 character codice fiscale of a person,
  with omocodia letters for digits, a real birth day and month, and the
  check letter (`chut.it_cf_check`); and an organization's 11 digit
  codice fiscale, the same as its partita IVA: 7 digits not all zero, an
  office code 001-100, 120, 121, 888 or 999, and a Luhn check digit,
  optionally after `IT`. Macie says only "Codice Fiscale", but its
  keywords include `p. iva` and `partita i.v.a.`. **Going beyond Macie:**
  when a check is clearly described, we may detect a little more than
  Macie documents, at the margin, where it makes sense and is doable
  (David, 2026-11-03).

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
10. Spain DNI: does Macie need the control letter, or does it report 8
    digits alone (its exclusions `99999999` and `99.999.999` have no
    letter)? Does it check the letter? NIE and Aadhaar formats are the
    issuers'. The short Spanish keywords match as substrings (item 3):
    `nie` in `niece`, `tin` in `setting`.
11. NIR, CURP and Codice Fiscale formats are the issuers'. Does Macie
    detect Italy's 11 digit organization codes (we do)? Does it accept NIRs with
    dots, or CURPs with sex X? python-stdnum also rejects Aadhaar
    numbers that are palindromes; we don't (over-reporting is the safer
    side), and Macie doesn't say.
12. Taxpayer numbers: does Macie detect 8 digit TFNs, TRNs, or the
    German Steuernummer (its keywords include `steuernummer`)? Which
    CUIT types does it count as organizations?
13. Does Macie's SPAIN_NIF_NUMBER also report NIEs and CIFs? Does it
    check the RFC check digit? How does it tell an individual's NIT from
    an organization's?
14. Credentials: does Macie require whole key blocks, or only the BEGIN
    line? Does it report AWS secret keys that are hex, or Basic headers
    whose token does not decode to user:password? Does it report Stripe
    restricted (rk_) keys?
15. US health: does Macie accept any DEA registrant type letter, MBIs
    with dashes, NDCs without hyphens, and CPT codes for HCPCS? Does it
    detect Railroad Retirement Board HICNs?
16. Does Macie need sentinels on magnetic stripe data, or both tracks?
    Does it check the identity card's check digit?
17. Group B: does Macie report a bank account number touching letters
    (`acct123456789`)? Does it accept NINOs spaced other than
    `AB 12 34 56 C`?
18. Passports: does Macie report one number under two countries when
    their shapes and keywords overlap? Does it accept Spain's older two
    letter form?
19. Phones: when a national number fits several countries' plans, does
    Macie report it for each, or does it choose one? How tight are its
    plans for Germany and Italy?
20. Dates: does Macie accept dotted dates (05.11.1985), month names in
    other languages, or ambiguous 8 digit dates?
21. Driver's licenses: how does Macie tell countries apart when their
    formats and keywords overlap? Which US state formats does it accept?
22. The rest of group B: which Brazil RG state formats does Macie
    accept? Does it match keywords without their accents (`cedula`)? Does
    it report an Argentine DNI as Spain's (it says it might)?
23. GPS and cookies: does Macie accept coordinates without a decimal
    part, or separated only by spaces? Does it count a Cookie header with
    several pairs as one occurrence, or one per pair?
24. Canada health numbers: which provinces does Macie detect, and with
    what checks? Ours misses Alberta, Manitoba, Saskatchewan, the
    Atlantic provinces and the territories.
25. EHIC and UDI: does Macie read the EHIC card number as 80 and a
    country code, and does it detect the personal ID on the card? Does it
    detect UDIs without their parentheses, or ISBT 128?
26. Spain SSN: does Macie check the NAF's control digits (commonly
    described as mod 97 of the first 10; no authoritative source found),
    and which layouts does it accept?

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
