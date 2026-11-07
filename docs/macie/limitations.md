# Limitations and road-test feedback

This is a first release. Below is what it does not do yet, where our
stand-ins are knowingly narrower than Macie, and where we want feedback
from people running it against real data.

## Not built yet

- **Downloading a wrapper from AWS.** The wrapper format is designed for
  a download from your account (the Macie API and S3, with the AWS
  responses kept verbatim), but the download is not built yet. Today a
  wrapper is a file you provide. Loading and running never call AWS.
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
| Driver's licenses for Finland, Greece, Hungary, Ireland, Latvia, Lithuania, Luxembourg, Malta, the Netherlands, Poland, Portugal, Romania, Slovakia, Slovenia, Sweden | Planned. The other 17 driver's license identifiers, including the US one (the union of the states' formats), are supported. |

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
| `MEDICAL_DEVICE_UDI` | ICCBBA ISBT 128 UDIs; only GS1 and HIBCC |
| `CANADA_HEALTH_NUMBER` | Provinces other than British Columbia, Ontario and Quebec |

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

- **Short keywords match inside words.** Keywords match as substrings,
  which is our reading of Macie's documentation. Brazil's `rg` matches `org`, `large` or a `cargo`
  column; `cep` matches `receptor` and `exception`; also `mc`, `pan`,
  `card`, `med`, `blood` and France's `social`. A value of the right
  shape next to such a word is reported. The [project
  rulesbase](customizing.md) can drop a keyword.
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
  UDI must be written with its parentheses.
- **Separators and layouts.** We accept the common printed layouts of
  card numbers, IBANs, national ids and phone numbers. Macie's own
  documentation is sometimes narrower (for example, it describes card
  numbers only as digit sequences), so we may report some values Macie
  would not.

## Data

The Macie functions check every cell of the CSV data CsvPath reads.
Macie also reads documents, archives and other file types; this does not.
A wrapper holds your allow lists' entries, which may be real names or
numbers: treat a wrapper as at least as sensitive as the lists it came
from.
