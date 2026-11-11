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
false positives.
