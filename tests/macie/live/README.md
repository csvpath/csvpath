# The live check against Amazon Macie

One run of the Framework's Macie support against a real AWS account
(`specs/macie/download-design.md`, Testing). It checks the download
(`add_named_paths_from_macie()`) against live AWS, and compares our
findings with Macie's own findings on the same files: the first fidelity
check. Not part of the test suite; run once, with David's OK.

## 1. Make the files

```
poetry run python tests/macie/live/make_live_files.py ~/macie-live
```

writes, all synthetic (nothing real), about 200 KB each:

```
~/macie-live/
  data/
    employees.csv      the custom identifier, its keywords, ignore word, both allow lists
    payments.csv       cards (with and without keywords), expiry, CVV, US bank account, IBANs
    people_us.csv      SSN, ITIN, phones, birth date, passport, driver's license, names, addresses
    people_eu.csv      UK NINO and NHS, France NIR, Germany ID, Spain DNI, NIE, SSN, Italy CF
    latam_health.csv   CPF, CNPJ, RUT, CURP, NPI, MBI, DEA, NDC
    credentials.csv    a fake AWS secret key, a Basic auth header
    clean.csv          nothing sensitive
  macie-config/allow/contractors.txt   the words allow list
  expected.json        what our stand-ins find, cell by cell (do not upload)
```

`tests/macie/test_macie_live_files.py` checks that every expectation holds
for our stand-ins, so a difference from Macie is about Macie, not a badly
built value. The files are not committed: credential-shaped values, even
fake ones, trip GitHub's push protection.

## 2. Set up AWS (David)

One region (e.g. `us-east-1`) and one bucket, e.g.
`csvpath-macie-test-<suffix>`:

- upload `data/*.csv` under `data/`;
- upload `macie-config/allow/contractors.txt` under `macie-config/allow/`.

**Enable Macie** in the region. If the console asks for a repository for
sensitive data discovery results (an S3 bucket and KMS key), set one up;
we do not read it.

**In Macie, create:**

1. **Custom data identifier** `EmployeeId`:
   - regex `EMP-\d{6}`
   - keywords `employee id`, `emp id`
   - ignore words `EMP-000000`
   - maximum match distance `50`
   - severity: 1 occurrence Low, 5 Medium, 10 High
2. **Allow list** `training-accounts`: regex `EMP-9\d{5}`.
3. **Allow list** `contractors`: predefined text,
   `s3://<bucket>/macie-config/allow/contractors.txt`.
4. **Two one-time jobs**, each on the bucket with an object criterion of
   key prefix `data/` (so the allow-list file is not scanned), each with
   `EmployeeId` and both allow lists:
   - **Job A, `csvpath-live-recommended`**: managed data identifiers
     **Recommended**.
   - **Job B, `csvpath-live-include`**: managed data identifiers
     **Custom**, *include* these 24:

     ```
     CREDIT_CARD_NUMBER
     CREDIT_CARD_NUMBER_(NO_KEYWORD)
     CREDIT_CARD_EXPIRATION
     CREDIT_CARD_SECURITY_CODE
     BANK_ACCOUNT_NUMBER
     UK_BANK_ACCOUNT_NUMBER
     GERMANY_BANK_ACCOUNT_NUMBER
     USA_SOCIAL_SECURITY_NUMBER
     USA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER
     PHONE_NUMBER
     DATE_OF_BIRTH
     DRIVERS_LICENSE
     USA_PASSPORT_NUMBER
     UK_NHS_NUMBER
     BRAZIL_CPF_NUMBER
     BRAZIL_CNPJ_NUMBER
     CHILE_RUT_NUMBER
     MEXICO_CURP_NUMBER
     USA_NATIONAL_PROVIDER_IDENTIFIER
     USA_MEDICARE_BENEFICIARY_IDENTIFIER
     US_DRUG_ENFORCEMENT_AGENCY_NUMBER
     USA_NATIONAL_DRUG_CODE
     NAME
     ADDRESS
     ```

     The recommended set (Job A) covers the European identifiers and the
     credentials; this list covers what it does not, plus `NAME` and
     `ADDRESS`, which we do not support, to see what Macie finds.
5. **Optional: automated sensitive data discovery.** Enable it, and add
   `EmployeeId` to its settings, so the template download is checked too.

**A read-only identity** for the check, e.g. a CLI profile
`csvpath-macie-reader`, with the policy from `docs/macie/aws.md`, plus:

- `s3:GetObject` on `arn:aws:s3:::<bucket>/macie-config/allow/contractors.txt`
- `macie2:ListFindings` and `macie2:GetFindings`, to read Macie's findings
  for the comparison

No write permissions, and no access to `data/`: our side runs on the same
local files.

## 3. Hand over

The region, the profile name, the two job ids, and an OK to run once both
jobs show **Complete**.

## 4. The run (Claude, with David's OK)

1. `add_named_paths_from_macie()` for each job (and `template=True` if
   step 5 was done), timed.
2. Run each group against `~/macie-live/data/*.csv`, timed.
3. `ListFindings` and `GetFindings` for each job; compare per file and
   identifier: count, severity, and the up to 15 cell locations Macie
   reports.
4. A fidelity report: what matched, what differed and why, which of the
   open fidelity questions (`specs/macie/transpile-design.md`) it settles,
   and the timings.

**Cost:** Macie bucket inventory about $0.10 a month, jobs about $1 per GB
scanned (these files are about 1.4 MB), automated discovery fractions of a
cent, S3 pennies. Well under a dollar; the 30-day trial covers most of it.

## 5. The second probe (2026-11-11)

The first check (`specs/macie/live-check-2026-11-11.md`) left three
differences open: a phone number with a country code and no keyword, a
German ID card number, and a Codice Fiscale, all reported by us and not
by Macie. The probe puts one variant per row, so Macie's cell locations
show which variants it reports.

```
poetry run python tests/macie/live/make_probe_files.py ~/macie-live
```

writes `~/macie-live/probe/` (`probe_phones.csv`, `probe_de_id.csv`,
`probe_it_cf.csv`, under 1 KB each) and `~/macie-live/expected_probe.json`
(do not upload).

**Set up (David):**

- upload `probe/*.csv` under `probe/` in the same bucket;
- create one one-time job, **`csvpath-probe-1`**:
  - object criterion: key prefix `probe/`;
  - managed data identifiers **Custom**, *include* these 3:
    `PHONE_NUMBER`, `GERMANY_NATIONAL_IDENTIFICATION_NUMBER`,
    `ITALY_NATIONAL_IDENTIFICATION_NUMBER`;
  - no custom identifiers, no allow lists.

**Hand over** the job id once it shows **Complete**. The reader profile
needs nothing new.

## 6. The third probe (2026-11-15)

The second probe found that `codice fiscale` is not a keyword to Macie,
although it contains the documented keyword `codice fiscal`. We match
managed identifiers' keywords as substrings; this probe asks whether
Macie matches them as words. Each keyword appears alone (the control)
and inside a longer word, as a column header and in a cell. It also asks
whether the two phone forms Macie reported without a keyword hold for
the UK and Germany.

```
poetry run python tests/macie/live/make_probe_files.py ~/macie-live 2
```

writes `~/macie-live/probe2/` (`probe2_keywords.csv`, `probe2_phones.csv`)
and `~/macie-live/expected_probe2.json` (do not upload).

**Set up (David):**

- upload `probe2/*.csv` under `probe2/` in the same bucket;
- create one one-time job, **`csvpath-probe-2`**:
  - object criterion: key prefix `probe2/`;
  - managed data identifiers **Custom**, *include* these 5:
    `USA_SOCIAL_SECURITY_NUMBER`,
    `USA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER`, `DATE_OF_BIRTH`,
    `ITALY_NATIONAL_IDENTIFICATION_NUMBER`, `PHONE_NUMBER`;
  - no custom identifiers, no allow lists.

**Hand over** the job id once it shows **Complete**.

## 7. The fourth probe (2026-11-16)

The second probe found Macie reports a `+1` number with no keyword only
when it is unbroken (`+12125550148`) or has a group in parentheses
(`+1 (212) 555-0148`). Our rule applies that to every country's phone
identifier; this probe checks the other six. Each country's number in
four forms with no keyword (unbroken, parentheses, spaces, dashes), and
once after the keyword `phone`.

```
poetry run python tests/macie/live/make_probe_files.py ~/macie-live 3
```

writes `~/macie-live/probe3/probe3_phones.csv` and
`~/macie-live/expected_probe3.json` (do not upload).

**Set up (David):**

- upload `probe3/probe3_phones.csv` under `probe3/` in the same bucket;
- create one one-time job, **`csvpath-probe-3`**:
  - object criterion: key prefix `probe3/`;
  - managed data identifiers **Custom**, *include* these 6:
    `UK_PHONE_NUMBER`, `FRANCE_PHONE_NUMBER`, `GERMANY_PHONE_NUMBER`,
    `ITALY_PHONE_NUMBER`, `SPAIN_PHONE_NUMBER`, `BRAZIL_PHONE_NUMBER`;
  - no custom identifiers, no allow lists.

**Hand over** the job id once it shows **Complete**.

## 8. The fifth probe (2026-11-17)

The fourth probe found that, outside the US, a number with its group in
parentheses is not reported without a keyword, an international number
with spaces is not reported even after a keyword, and Germany's and
Italy's unbroken numbers were not reported. This probe asks what the
fourth could not: national numbers after a keyword (in the cell and as
the column header), an international number with spaces under a `phone`
header, other unbroken numbers for Germany and Italy, and Brazil, which
the fourth probe's job left out.

```
poetry run python tests/macie/live/make_probe_files.py ~/macie-live 4
```

writes `~/macie-live/probe4/probe4_phones.csv` and
`~/macie-live/expected_probe4.json` (do not upload).

**Set up (David):**

- upload `probe4/probe4_phones.csv` under `probe4/` in the same bucket;
- create one one-time job, **`csvpath-probe-4`**:
  - object criterion: key prefix `probe4/`;
  - managed data identifiers **Custom**, *include* all 6:
    `UK_PHONE_NUMBER`, `FRANCE_PHONE_NUMBER`, `GERMANY_PHONE_NUMBER`,
    `ITALY_PHONE_NUMBER`, `SPAIN_PHONE_NUMBER`, **`BRAZIL_PHONE_NUMBER`**;
  - no custom identifiers, no allow lists.

**Hand over** the job id once it shows **Complete**.

## 9. The sixth probe (2026-11-17): headers (#479)

How does Macie read a CSV whose first line is not the header? Our runs
take the first line as the header, so a file with no header, or with a
title line first, loses every finding that depends on a header keyword,
silently (pair 01's data: 8 findings, 3 without a header or after a title
line). If Macie reads such files the same way, we match it and add a
warning; if it reads them better, we add a way to say where the header
is.

```
poetry run python tests/macie/live/make_probe_files.py ~/macie-live 5
```

writes `~/macie-live/probe5/`: the same rows three ways,
`header_normal.csv` (a header), `header_none.csv` (no header) and
`header_title.csv` (a title line, then the header). Two SSNs are found
only through the `ssn` header; one through `ssn` in its own cell, the
control. Do not upload `~/macie-live/expected_probe5.json`.

**Set up (David):**

- upload the three files in `probe5/` under `probe5/` in the same
  bucket (check they are there before creating the job);
- create one one-time job, **`csvpath-probe-5`**:
  - object criterion: key prefix `probe5/`;
  - managed data identifiers **Custom**, *include*
    `USA_SOCIAL_SECURITY_NUMBER`;
  - no custom identifiers, no allow lists.

**Hand over** the job id once it shows **Complete**.
