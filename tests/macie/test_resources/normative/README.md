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
    expected.yaml            per run: data file, finding_lines, and why
                             each line does or doesn't have a finding

Design decisions are in `specs/macie/transpile-design.md`.

## Pairs

- `01_employee_ids`: one custom data identifier (keywords in headers and
  in cells, maximum match distance, ignore word, severity thresholds), one
  regex allow list, a detail cap of 3. No managed identifiers.

Planned:

- `02_credit_card`: `CREDIT_CARD_NUMBER` stand-in (Luhn, issuer prefixes,
  keywords optional), plus a text allow list via `load_list()`.
- `03_breaker`: the global breaker trips, `stop()`, partial report.
