# Live check against Amazon Macie, 2026-11-11

The first run of the Framework's Macie support against a real AWS account,
as set out in `tests/macie/live/README.md`. Account 724414611418,
`us-east-1`.

## What ran

| Job | Id | Managed identifiers |
|---|---|---|
| `csvpath-live-include` | `cebd418bcb8fc253596c61440eb3157a` | include, 24 ids |
| `csvpath-live-recommended` | `0a72a26beda4821399e1af90406c307e` | Recommended (35, `jobs-recommended@2026-11-08`) |

Both with the custom identifier `EmployeeId` and the allow lists
`training-accounts` (regex) and `contractors` (S3 words list), on the seven
files under `data/`. (The README called these Job B and Job A.)

The uploaded files are byte-identical to a local
`make_live_files.py` run (S3 ETags equal the local MD5s), so our side ran on
exactly what Macie scanned.

## The download

Run as `macie-test-user`, whose only permissions are the policy in
`docs/macie/aws.md` (plus `ListFindings`/`GetFindings`), under a
permissions boundary.

| | `include` | `recommended` |
|---|---|---|
| `MacieDownloader.download_job()` | 1.38 s | 1.03 s |
| `add_named_paths_from_macie()` | 2.54 s | 1.06 s |
| Managed identifiers resolved | 24 | 35 |
| Custom identifiers | 1 | 1 |
| Allow lists | 2, both `OK` (words file read) | 2, both `OK` |
| Warnings | none | none |

The policy in `docs/macie/aws.md` is sufficient: no access errors.

## Our runs

Each group against each of the seven files, one `collect_paths()` per file:
1.45 to 1.70 s per file for `include`, 1.97 to 2.68 s for `recommended`
(35 identifiers). All runs valid.

## The comparison

Per job, file and identifier: occurrence count and cell locations
(row, column).

**34 of 43 match exactly.** The 9 that differ:

| Job | File | Identifier | Macie | Ours | Why |
|---|---|---|---|---|---|
| both | employees | EmployeeId | 3 occurrences, 2 cells | 3 occurrences, 3 cells | **Our bug.** Macie lists a cell once even when it holds two occurrences; we list it once per occurrence. Counts agree. |
| include | people_us | PHONE_NUMBER | 1 | 2 | `call +1 212 555 0148` in `notes`: Macie does not report it. Our rule: a country code needs no keyword. Open (see below). |
| recommended | people_eu | GERMANY_NATIONAL_IDENTIFICATION_NUMBER | 0 | 1 | `HCYFH089R5` under `personalausweis`: Macie does not report it. Open. |
| recommended | people_eu | ITALY_NATIONAL_IDENTIFICATION_NUMBER | 0 | 1 | `RSSMRA85T10A562S` under `codice_fiscale`: Macie does not report it. Open. |
| include | payments, people_eu, people_us | NAME | 1 each | 0 | Not supported, as expected. |
| include | people_us | ADDRESS | 1 | 0 | Not supported, as expected. |

**File-level severity matches in all 14 job-file pairs** (the highest
severity among our detections equals Macie's finding severity), and files
with nothing found have no Macie finding.

**Expectations** (`expected.json`, including the negative ones): of 68
expectation-job checks where the job ran the identifier, Macie agrees with
65. The 3 that differ are the phone, German ID and Codice Fiscale above.

## What it settles

Confirmed, matching our implementation:

- **Custom identifiers:** the keyword variant rule applies to custom
  identifiers too (`employee id` matches header `employee_id`,
  interpretation 2); case-sensitive regex; ignore words; the 50-character
  maximum match distance; two occurrences in one cell count twice.
- **Allow lists:** both the regex list and the S3 words list suppress
  occurrences. (Interpretation 1, occurrence text against the whole cell, is
  not settled: the allow-listed cell held only the value.)
- **Cards:** Luhn is required; keyword and no-keyword variants split as we
  split them; **grouped 4-4-4-4 numbers are detected** (fidelity item 2).
- **Banking:** US bank account by header keyword; UK and German IBANs with no
  keyword.
- **Spain DNI needs the control letter** (fidelity item 10): a wrong letter
  is not reported.
- **Spain SSN** (fidelity item 26): Macie reported the value we report on
  format alone. Whether it checks the control digits is not settled: the
  value's control digits may have been valid.
- **Brazil CPF:** repeated digits are rejected. CNPJ, RUT, CURP, NPI, MBI
  (with dashes), DEA and NDC (4-4-2) all agree.
- **Credentials:** `AWS_CREDENTIALS` with the keyword in the cell, and not at
  the wrong length; a complete Basic auth header.
- **UK NINO, NHS (mod 11), France NIR (mod 97), Spain NIE**, a US SSN, ITIN,
  passport and driver's license by header keyword (`drivers_license`: the
  `_` variant works for managed identifiers), and a date of birth.

## Open, needing a second probe

1. **Phones with a country code and no keyword.** Is it the country-code
   rule, or the space-separated grouping (`+1 212 555 0148`)? A probe with
   `+12125550148`, `+1-212-555-0148` and `+1 (212) 555-0148`, each with and
   without a keyword, would tell.
2. **Germany ID.** Is `HCYFH089R5` (the 2010 card format, ICAO check digit)
   outside what Macie accepts? Probe the older 9 digit plus check digit
   format, the same value with the keyword in the cell, and a second valid
   new-format number.
3. **Codice Fiscale.** `RSSMRA85T10A562S` is the common textbook example,
   valid check letter, header keyword variant. Probe with the keyword in the
   cell (`codice fiscale: ...`), and with other generated values, to tell a
   keyword problem from a value check (birth date, municipality code)
   that we do not do.

Each is a short file and one more job: cents.

## Fixed on our side

- **Cell list per identifier:** one entry per cell, not per occurrence, to
  match Macie's `occurrences.cells`. The count stays per occurrence
  (`IdentifierTally.record`; six normative pairs' expected findings lost
  a duplicate cell).

Until the open items are probed, the phone, German ID and Codice Fiscale
differences go on the worklist's "Ask road-testers about" list as possible
false positives. (Probed on 2026-11-14: see the next section.)

## The second probe, 2026-11-14

Job `csvpath-probe-1` (`3347c6fce7a5889680d5e436c77d676d`): include
`PHONE_NUMBER`, `GERMANY_NATIONAL_IDENTIFICATION_NUMBER`,
`ITALY_NATIONAL_IDENTIFICATION_NUMBER`; the three files from
`tests/macie/live/make_probe_files.py` under `probe/` (ETags equal the
local MD5s). One variant per row; Macie reported 2 findings, 6 cells.

### Phones

| Cell | Ours | Macie |
|---|---|---|
| `call +1 212 555 0148` | 1 | 0 |
| `call +12125550148` | 1 | **1** |
| `call +1-212-555-0148` | 1 | 0 |
| `call +1 (212) 555-0148` | 1 | **1** |
| `call +1.212.555.0148` | 1 | 0 |
| `call +44 20 7946 0958` | 0 | 0 |
| `call +49 30 12345678` | 0 | 0 |
| `+1 212 555 0148` under header `phone` | 1 | 1 |
| `phone +1 212 555 0148` | 1 | 1 |
| `phone 212 555 0149` | 1 | 1 |

With a keyword, Macie takes spaces. **Without one, a country code is not
enough**: only the unbroken `+12125550148` and the `(212)` form were
reported; spaces, dashes and dots between the groups were not. Our rule
(a country code needs no keyword) over-reports.

### German ID

Macie reported **none** of seven variants: the first check's value under
the `personalausweis` header and with `personalausweis:` in the cell,
three more 2010-format values (valid ICAO check digit), one after
`ausweisnummer`, and a pre-2010 all-digit number. The keyword is not the
problem (it is on Macie's list and was in the cell), so Macie checks
something about the value that we do not, or detects a form we have not
tried. We report all seven.

### Codice Fiscale

| Cell | Ours | Macie |
|---|---|---|
| `RSSMRA85T10A562S` under `codice_fiscale` | 1 | 0 |
| the same under `codice fiscale` | 1 | 0 |
| `codice fiscale: RSSMRA85T10A562S` | 1 | 0 |
| three more values under `codice_fiscale` | 1 each | 0 |
| `tax code BNCLRA70A41H501B` | 1 | **1** |

The value check is not the problem: `BNCLRA70A41H501B` was reported after
`tax code` and not under `codice_fiscale`. **`codice fiscale` is not a
keyword to Macie**, in the header or in the cell, with a space or an
underscore. Our catalog, copied from Macie's documentation, lists the
keyword as `codice fiscal`, and we match keywords as substrings (fidelity item 3), so for us
`codice fiscale` contains it. For Macie it does not.

That is the first evidence on item 3: **Macie may match managed
identifiers' keywords as whole words, not substrings.** If so, every
keyword that fires inside a longer word for us (Brazil's `rg` in `org`,
`cep` in `receptor`, `card`, `pan`, ...) over-reports, not just this one.
It may instead be that the documented `codice fiscal` is a typo and the
real keyword is something else; one more probe can tell the two apart.

### What to decide

1. **Phones:** a country code without a keyword counts only for the
   unbroken E.164 form and the `+1 (212) 555-0148` form. Narrowing our
   rule to that matches all ten rows.
2. **Keywords: substrings or words?** A short probe: a few identifiers
   whose keywords we can put inside longer words (`ssn` in `ssnumber`,
   `itin` in `itinerary`, `dob` in `dobson`), and the same keywords
   standing alone as controls. If Macie matches words, change the keyword
   rule for managed identifiers (custom identifiers stay as tested in the
   first check, where the keyword stood alone).
3. **German ID:** nothing we tried is reported. Until a reported form is
   found, our stand-in can only over-report against Macie. Options: mark
   it partial in the catalog and say so in `limitations.md`, or probe
   further (the MRZ form with `D` and `<` fillers, the number with the
   card's own `IDD` prefix).

### Decided (David, 2026-11-15)

- **German ID:** marked partial in the catalog ("Not confirmed against
  Macie"), so every conversion that uses it says so; listed in
  `docs/macie/limitations.md` under "Known to differ from Macie". Probing
  the machine-readable forms is deferred.
- **Keywords:** a third probe (`tests/macie/live/README.md` section 6),
  before any change to the keyword rule.
- **Phones:** waiting on the third probe, which adds the UK and German
  numbers in the two forms Macie reported without a keyword.

## The third probe, 2026-11-15

Job `csvpath-probe-2` (`deafd731404e74a81bd409f9a5b3329e`): include
`USA_SOCIAL_SECURITY_NUMBER`, `USA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER`,
`DATE_OF_BIRTH`, `ITALY_NATIONAL_IDENTIFICATION_NUMBER`, `PHONE_NUMBER`;
the files from `make_probe_files.py <out> 2` under `probe2/` (ETags equal
the local MD5s).

### Keywords: words, not substrings

| Where the keyword is | Ours | Macie |
|---|---|---|
| header `ssn` | 1 | 1 |
| header `ssnumber` | 1 | **0** |
| header `customer_ssn` | 1 | 1 |
| cell `ssn 716-90-7411` | 1 | 1 |
| cell `myssn 644-25-1556` | 1 | **0** |
| header `itin` | 1 | 1 |
| header `itinerary` | 1 | **0** |
| header `dob` | 1 | 1 |
| header `dobson` | 1 | **0** |
| header `codice fiscal` | 1 | 1 |
| header `tax code` | 1 | 1 |

**Settled (fidelity item 3): Macie matches managed identifiers' keywords
as whole words.** A keyword inside a longer word, at its start, end or
middle, does not count; `_` separates words (`customer_ssn`). The
documented `codice fiscal` is a real keyword, and that is why
`codice fiscale` (a longer word) was not one in the second probe.

### Phones for other countries

None of `+442079460958`, `+44 (20) 7946 0958`, `+493012345678`,
`+49 (30) 12345678` (no keyword) was reported, by Macie or by us; the
`+12125550148` control was reported by both. Without a keyword, only the
two `+1` forms have been seen reported.

### Changed (David, 2026-11-15)

- **Keywords match as whole words**, for managed and custom identifiers
  (`KeywordUtility.is_word`): a keyword edge that is a letter or digit
  must not touch another letter or digit.
- **Phones:** a number with a country code needs no keyword only when it
  is unbroken or has a group in parentheses (`PhoneDetector.keyword_exempt`).
- With both, our stand-ins agree with Macie on every row of the live
  files and both probes except the seven German IDs (partial). Normative
  pairs 11 (two Codice Fiscale codes under `codice_fiscale`) and 19 (four
  international numbers written with spaces and no keyword) changed
  accordingly.

## The template download, 2026-11-16

`add_named_paths_from_macie(template=True)`, live for the first time,
after David enabled automated sensitive data discovery and added
`EmployeeId` to its settings. As `macie-test-user`, with the docs policy:

- `MacieDownloader.download_template()`: 1.22 s, no warnings. Template
  `a0406f6b5a62d76d4036166a7132f4d8`; selector `RECOMMENDED`, resolved to
  35 identifiers from `automated-discovery-recommended@2026-11-08` (the
  account was first enabled after 2023-08-02, so not the static set of
  100); `EmployeeId`; no allow lists.
- Loaded as a group: 0.98 s; the home holds
  `automated-sensitive-data-discovery.macie.json` and its report; the
  manifest's `source_path` is
  `aws:macie2:us-east-1:724414611418:sensitivity-inspection-template/a0406f6b5a62d76d4036166a7132f4d8`.
- Run on `people_us.csv`: valid, and the same four identifiers as Job
  `csvpath-live-recommended` found there (driver's license, ITIN,
  passport, SSN).

The static set of 100 (accounts first enabled before 2023-08-02) can be
checked only with stubbed responses.

## The fourth probe, 2026-11-16: phones outside the US

Job `csvpath-probe-3` (`49d371bb0e2d9a2cb3633eb3d502ea3a`), the file from
`make_probe_files.py <out> 3` under `probe3/` (ETag equal to the local
MD5). The job ran five of the six identifiers: `BRAZIL_PHONE_NUMBER`,
which the account offers, was not in it, so the Brazil rows are untested.

| Form | UK | France | Germany | Italy | Spain | Ours |
|---|---|---|---|---|---|---|
| unbroken, no keyword | 1 | 1 | **0** | **0** | 1 | 1 |
| group in parentheses, no keyword | **0** | **0** | **0** | **0** | **0** | 1 |
| spaces, no keyword | 0 | 0 | 0 | 0 | 0 | 0 |
| dashes, no keyword | 0 | 0 | 0 | 0 | 0 | 0 |
| `phone` and spaces | **0** | **0** | **0** | **0** | **0** | 1 |

15 of 30 rows agree. Three things:

1. **Parentheses are a US form.** The `+1 (212) 555-0148` form Macie
   reported in the second probe is not reported for any of the five
   other countries.
2. **An international number written with spaces is not reported even
   after a keyword**, in all five countries. For the US it was (`phone
   +1 212 555 0148`, second probe). National numbers after a keyword
   (`tel 06 12 34 56 78`, pair 19) are not yet checked live.
3. **Germany's and Italy's unbroken numbers were not reported**, where
   the UK's, France's and Spain's were. `+4930123456` (a six digit Berlin
   subscriber number) and `+393123456789` may fail a stricter numbering
   plan check than ours; one number each does not say.

## The fifth probe, 2026-11-17: phones outside the US, continued

Job `csvpath-probe-4b` (`c162f5d55bfd644cf412fb59aeef0ef9`; the first,
`356c69b3...`, ran before the file was uploaded and scanned nothing), all
six identifiers, the file from `make_probe_files.py <out> 4` under
`probe4/` (ETag equal to the local MD5). 16 of 31 rows agree.

| Form | UK | France | Germany | Italy | Spain | Brazil | Ours |
|---|---|---|---|---|---|---|---|
| national, `tel` in the cell | 1 | 1 | **0** | **0** | **0** | 1 | 1 |
| national, `phone` header | 1 | 1 | **0** | **0** | **0** | 1 | 1 |
| international with spaces, `phone` header | **0** | **0** | **0** | **0** | **0** | 1 | 1 |
| unbroken, no keyword | 1 | 1 | 1, 1, 1 | **0, 0** | 1 | 1, 1 | 1 |
| Brazil only: parentheses, no keyword | | | | | | **0** | 1 |
| Brazil only: `phone` in the cell, spaces | | | | | | **0** | 1 |

Every number in the probe is valid by Google's `phonenumbers`
(`is_valid_number`), so the misses are not invalid numbers.

### With the fourth probe

| | UK | France | Germany | Italy | Spain | Brazil |
|---|---|---|---|---|---|---|
| unbroken, no keyword | 2 of 2 | 2 of 2 | 3 of 4 | **0 of 3** | 2 of 2 | 2 of 2 |
| parentheses, no keyword | 0 of 1 | 0 of 1 | 0 of 1 | 0 of 1 | 0 of 1 | 0 of 1 |
| international with spaces or dashes, any keyword | 0 of 2 | 0 of 2 | 0 of 2 | 0 of 2 | 0 of 2 | 1 of 2 (header yes, cell no) |
| national after a keyword | 2 of 2 | 2 of 2 | **0 of 2** | **0 of 2** | **0 of 2** | 2 of 2 |

What holds across the countries:

1. **An international number counts when unbroken**: 11 of 12 outside
   Italy. The miss is `+4930123456`, a short Berlin number.
2. **Parentheses are a US form** (0 of 6), and **an international number
   written with spaces or dashes is not reported** (1 of 12, Brazil
   under a header).

What does not, and is not explained by the format:

3. **Italy: nothing reported**, in 8 rows over the two probes, in any
   form, with or without a keyword.
4. **National numbers after a keyword**: reported for the UK, France and
   Brazil; not for Germany, Italy or Spain, with the same keywords.
