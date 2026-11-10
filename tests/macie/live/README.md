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
