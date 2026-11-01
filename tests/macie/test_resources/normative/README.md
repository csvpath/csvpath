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
  and a 20-digit run. A text allow list waits for `load_list()` (#470).
- `03_breaker`: two custom identifiers, `max_findings` 5 and a detail cap
  of 2. The global breaker trips between two occurrences in one cell; the
  second identifier is not applied on that line; the run stops, and the
  stopping line still matches (#483). The summary and the stopped message
  print at the trip, and findings record `stopped_at_line`.
