# Macie -> CsvPath normative pairs

Each subdirectory is one normative pair: a Macie wrapper
(`*.macie.json`, see `specs/macie/wrapper-format.md`) and the csvpath the
transpiler must produce from it, plus data and expected results that prove
the csvpath behaves like Macie.

Layout of a pair:

    <name>.macie.json        the wrapper (input)
    expected/<name>.csvpath  transpiler output, exact
    expected/printouts.<stream>.txt
                             printouts of one print stream, exact
                             (Macie output uses the "macie" stream)
    expected/findings.json   the run's macie_findings variable, in Macie's
                             detections shape
    data/*.csv               sample data
    expected.yaml            conversion: the MacieConverter.convert()
                             arguments that produce expected/<name>.csvpath;
                             per run: data file, finding_lines, and why
                             each line does or doesn't have a finding

The tests check that MacieConverter produces the expected csvpath
exactly, and that both the expected csvpath and the converter's output
give every expected result in a real run.

Design decisions are in `specs/macie/transpile-design.md`.

## Pairs

- `01_employee_ids`: one custom data identifier (keywords in headers and
  in cells, maximum match distance, ignore word, severity thresholds), one
  regex allow list, a detail cap of 3. No managed identifiers.
- `02_credit_card`: the managed identifiers `CREDIT_CARD_NUMBER` and
  `CREDIT_CARD_NUMBER_(NO_KEYWORD)` as our stand-ins. Keywords in the
  header and before and after the number in a cell, a keyword too far
  away, grouped numbers, two cards in one cell, a bad check digit, a Luhn
  number with no brand prefix, an issuer test number, a regex allow list,
  and a 20-digit run.
- `03_breaker`: two custom identifiers, `max_findings` 5 and a detail cap
  of 2. The global breaker trips between two occurrences in one cell; the
  second identifier is not applied on that line; the run stops, and the
  stopping line still matches (#483). The summary and the stopped message
  print at the trip, and findings record `stopped_at_line`.
- `04_us_ids`: the managed identifiers `USA_SOCIAL_SECURITY_NUMBER` and
  `USA_NATIONAL_PROVIDER_IDENTIFIER`. Header and in-cell keywords, no
  keyword, the three SSN layouts, a never-issued area, an excluded
  example SSN, a bad NPI check digit, two SSNs in one cell, and an SSN and
  an NPI in the same cell.
- `05_iban`: three of the 52 IBAN identifiers (UK, Germany, Netherlands),
  using one parameterized detector. Contiguous, printed in groups of four,
  lower case with hyphens, in text, two countries in one cell; bad check
  digits, mixed separators, an unselected country, and a UK domestic sort
  code and account with no keyword nearby, which is not reported.
- `06_sin_nhs_vin`: Canada SIN, UK NHS number and VIN. Header and in-cell
  keywords, no keyword, the SIN example number, bad Luhn and mod 11 check
  digits, a European VIN with no check digit, a VIN with the letter O, and
  an NHS number and a SIN in the same cell.
- `07_latam`: Brazil CPF and CNPJ, Chile RUT and Argentina SUBE. Printed
  and contiguous forms, a RUT with check character K, a repeated-digit CPF
  and an all-zero RUT (both pass the check, neither is reported), bad
  check digits, SUBE with and without a keyword, and a RUT and a CPF in
  the same cell.
- `08_bban`: the BBANs of France, Germany, Italy, Spain and the UK, with
  keywords in the header and in the cell; a BBAN with no keyword (not
  reported); the UK sort code and account; a bad RIB key and bad Spanish
  check digits; IBANs with and without a keyword (always reported); and a
  German IBAN and BBAN in one cell.
- `09_text_allow_list`: pair 01's data and custom identifier with a text
  allow list as well as the regex one. The list is loaded with
  `load_list()` by its Macie id; an entry in another case still allows,
  one allowed occurrence leaves a line with no finding, and another
  leaves a second occurrence in the same cell. The normative runs write
  the list to a temp dir; in a group it is `assets/<id>.txt`.
- `10_es_in`: Spain DNI and NIE and India Aadhaar. Header and in-cell
  keywords, no keyword, a dotted DNI, a NIE with hyphens, wrong control
  letter, Macie's DNI example 99999999 and an all-zero NIE (both with the
  right letter, neither reported), an Aadhaar that passes Verhoeff but
  starts with 1, a bad Verhoeff digit, and two identifiers in one cell.
- `11_fr_mx_it`: France NIR (INSEE), Mexico CURP and Italy Codice
  Fiscale. A grouped NIR, a Corsican NIR, a bad key; CURPs born in the
  1900s and 2000s, one with no such state; a Codice Fiscale for a woman
  (day + 40), one with omocodia, one dated 30 February; two identifiers
  in one cell, lower case; no keyword; and an organization's 11 digit
  code (partita IVA) with an IT prefix, and one with a bad Luhn digit.
- `12_tax_ids`: Germany IdNr, Argentina CUIT and CUIL for individuals and
  organizations, Australia TFN and UK UTR. Grouped and contiguous forms;
  an IdNr with one digit three times and one with two digits repeated;
  the CUIT type deciding individual or organization (MEDIUM); bad check
  digits; an 8 digit TFN (not detected, the entry is partial); a UTR's
  leading check digit; a keyword with a hyphen; two identifiers in one
  cell; and no keyword.
