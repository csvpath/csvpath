# Limitations and road-test feedback

This is a first release. Below is what it does not do yet, where our
stand-ins are knowingly narrower than Macie, and where we want feedback
from people running it against real data.

## Not built yet

- **A live test of the download.** Reading a job from AWS
  ([getting the rules from AWS](aws.md)) is tested against AWS's own API
  definitions, offline. It has not yet been run against a live account;
  that check is planned. Loading a group and running it never call AWS.
- **A comparison with real Macie.** Our reading of Macie's documentation
  has not yet been checked by running the same files through Macie. The
  questions that comparison will answer are listed in
  `specs/macie/transpile-design.md` ("Interpretations to confirm"). Until
  then, treat findings as close to Macie's, not identical.

## Managed identifiers without a stand-in

| Identifier | Why |
|---|---|
| `NAME` | Macie uses machine learning to find names. |
| `ADDRESS` | An address needs a gazetteer of places and postal codes. |

A wrapper that selects one of these still loads. The conversion report
lists it as not translated, and the rest of the job runs.

## Partial stand-ins

These detect less than Macie says Macie detects. Each is marked in the
catalog, and every conversion that uses one says so in its report.

| Identifier | Not detected |
|---|---|
| `BRAZIL_CNPJ_NUMBER` | The alphanumeric CNPJs Brazil issues from July 2026; only numeric CNPJs |
| `AUSTRALIA_TAX_FILE_NUMBER` | The older 8 digit TFNs |
| `UK_TAX_IDENTIFICATION_NUMBER` | TRNs (temporary reference numbers); only UTRs |
| `USA_HEALTH_INSURANCE_CLAIM_NUMBER` | Railroad Retirement Board numbers; only SSN-based HICNs |
| `CANADA_HEALTH_NUMBER` | Provinces other than British Columbia, Ontario and Quebec |

## Known to differ from Macie

Found by running the same files through Macie and through the stand-ins
(`specs/macie/live-check-2026-11-11.md`). Each may report values Macie
does not.

- **`GERMANY_NATIONAL_IDENTIFICATION_NUMBER`**: Macie reported none of
  seven forms we tried, with valid check digits and the keyword in the
  header or the cell. Marked partial in the catalog, so every conversion
  that uses it says so in its report.

Two earlier differences were fixed by following Macie (2026-11-15):
keywords now match as whole words, so `codice fiscale` is not the
Italian keyword `codice fiscal`; and a phone number with a country code
needs no keyword only when it is unbroken (`+12125550148`) or, for the
US, has a group in parentheses (`+1 (212) 555-0148`). Outside the US an
international number is found only unbroken, keyword or not
(2026-11-17): Macie did not report `+44 (20) 7946 0958`, nor
`phone +44 20 7946 0958`.

Still different for phones (live probes, 2026-11-16 and -17, numbers
valid by Google's `phonenumbers`):

- **`ITALY_PHONE_NUMBER`**: Macie reported no Italian number in any form,
  with or without a keyword. We report them as we report other
  countries'.
- **German, Italian and Spanish national numbers after a keyword**
  (`tel 030 12345678`): Macie did not report them; UK, French and
  Brazilian ones it did. We report all six countries'.
- **A spaced Brazilian international number under a `phone` header** was
  reported by Macie; we no longer report it.

## Also not translated

- **Findings filters** act on findings after detection. They are kept in
  the wrapper and listed in the conversion report, not applied.
- **Job scope** (buckets, object criteria, sampling, schedules) is
  Macie's choice of what to scan. Here you choose the files, so it is
  kept as metadata only.

## What we want road-test feedback on

These are known false positive and false negative risks. If your data
shows any of them, we want to hear about it, with the identifier, a
description of the value (not the value), and the column name.

- **Keywords are whole words.** As Macie does (checked against Macie,
  2026-11-15), a keyword counts only as a word of its own: `ssn` in an
  `ssn` or `customer_ssn` column or in `SSN: ...`, not in `ssnumber` or
  `myssn`. `_`, `-`, spaces and punctuation separate words. A keyword
  written directly against a value, as in `SSN123-45-6789`, is not a
  word, which may miss some values; we have not seen what Macie does
  there.
- **Keywords need their accents.** `cedula de ciudadania` without its
  accents is not Colombia's keyword, so a cedula labeled that way is
  missed.
- **One value, several countries.** A national phone number can fit
  several countries' numbering plans, an 8 digit number near "driver
  license" fits the US, Canada and Australia, and digit runs are shared by
  the Argentina DNI, Colombia cedula and Canada PR number. Such a value is
  reported for each identifier selected.
- **Formats that are ours.** Where Macie publishes only keywords, the
  format is ours (fidelity tier B). For example: Brazil RG takes only Sao
  Paulo's shape; the Canada PR number is the immigration client number
  (UCI), not the card's document number; an EHIC is its 20 digit card
  number (80 and a country code), not the personal id on the card; a GS1
  UDI must be written with its parentheses, and an ISBT 128 UDI in its
  human readable form, starting `=/`; a Spanish Social Security
  number's control digits are not checked (we found no authoritative
  statement of the rule).
- **Separators and layouts.** We accept the common printed layouts of
  card numbers, IBANs, national ids and phone numbers. Macie's own
  documentation is sometimes narrower (for example, it describes card
  numbers only as digit sequences), so we may report some values Macie
  would not.

## Headers

A file with no header, or with a title line before the header, has no
header keywords, so a value found only through its column's header (an
SSN under `ssn`) is not reported. Macie behaves the same (live probe,
2026-11-18). A first line that holds a value is read as data and the run
says so; see [results](results.md). A title line holds no value, so it
is still read as the header, and its text names the columns; Macie
gives them no names, by a rule we do not know.

## Data

The Macie functions check every cell of the CSV data CsvPath reads.
Macie also reads documents, archives and other file types; this does not.
A wrapper holds your allow lists' entries, which may be real names or
numbers: treat a wrapper as at least as sensitive as the lists it came
from.
