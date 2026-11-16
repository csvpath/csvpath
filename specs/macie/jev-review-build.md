# Jev review: build design

2026-11-15. How the review from `jev-review-design.md` is built, after
the two experiments (`jev-experiment-2026-11-15.md`): `choice()` with
our own column facts got 29 of 30 right, for well under a cent.

The rules from the design note stand: values are masked; the review
annotates and never removes; it is off unless asked for, per
identifier; the model is pinned; what was asked and answered is
recorded.

## A run with the review on

`config.ini`:

```ini
[macie]
review = USA_SOCIAL_SECURITY_NUMBER, CREDIT_CARD_NUMBER
review_model = jev-1.14.0
review_max_questions = 50

[jev]
key = JEV_KEY
```

A file `orders.csv` with SSN-shaped values in `ref_no` (4,000 rows, all
the same value) and real SSNs in `ssn`. The run finds them as today;
then, after the last line, one Jev request asks one question per file,
column and identifier reviewed: here two.

Printouts gain one line per question:

```
macie USA_SOCIAL_SECURITY_NUMBER: 4012 occurrences, severity HIGH, detail shown for first 15
macie review USA_SOCIAL_SECURITY_NUMBER column 7 ref_no: unrelated (0.06); every value the same
macie review USA_SOCIAL_SECURITY_NUMBER column 3 ssn: likely (0.91)
macie review: 2 questions, jev-1.14.0, 0.4 s, 512 tokens in, 61 out
```

`macie_findings` keeps every count, severity and cell. Each reviewed
detection gains a `review` list, one entry per column:

```json
{
  "type": "USA_SOCIAL_SECURITY_NUMBER",
  "count": 4012,
  "severity": "HIGH",
  "occurrences": {"cells": ["..."]},
  "review": [
    {
      "column": 7,
      "columnName": "ref_no",
      "verdict": "unrelated",
      "confidence": 0.06,
      "probabilities": {"likely": 0.06, "doubtful": 0.21, "unrelated": 0.73},
      "facts": ["Every one of the 4000 flagged values is the same value."]
    },
    {
      "column": 3,
      "columnName": "ssn",
      "verdict": "likely",
      "confidence": 0.91,
      "probabilities": {"likely": 0.91, "doubtful": 0.07, "unrelated": 0.02},
      "facts": ["Every flagged value is different."]
    }
  ]
}
```

and the `csvpath` section gains the review's summary:

```json
"review": {
  "status": "complete",
  "model": "jev-1.14.0",
  "questions": 2,
  "input_tokens": 512,
  "output_tokens": 61,
  "seconds": 0.4
}
```

In a named-paths group run, `_extra_data/macie/review.json` holds the
exact request (state and questions, masked) and the response, so an
auditor can see what was asked. A standalone run has no run directory;
it prints and stores the variable only.

## The pieces

Three PRs, each with its own tests.

### 1. Column facts and masks (no Jev)

- `MaskUtility` (`maut`), in `csvpath/macie/util/`: `mask(text)` (each
  letter `A`, each digit `#`) and `mask_cell(text)` (mask each word
  holding a digit, keep the others). The experiment's two functions,
  moved into the package.
- `ColumnFacts`: collects, per identifier and column, during the scan:
  occurrences, the number of distinct cells (by a hash of the cell, so
  no value is kept), whether the digit-only cells are consecutive
  numbers, and up to 3 masked samples. Bounded: past 10,000 distinct
  cells it stops counting distinct values and says "at least". Its
  `facts()` gives the plain-words lines the second run used.
- Distinct values are counted by **cell**, not by match. A cell holding
  only the value counts the same either way; in a notes column, where
  each cell is different text, "every value different" is still right
  in practice. Counting matches would mean changing what
  `occurrences()` returns for every identifier, and it is not needed
  yet.

### 2. The reviewer

- `JevReviewer` builds the request (the experiment's state, one
  `choice()` per file, column and identifier, likely / doubtful /
  unrelated) from `ColumnFacts`, sends it, and maps answers to review
  entries. The client comes from a factory, so tests pass a fake and
  never reach the network.
- `review_max_questions` is a breaker: past it, the rest are listed as
  not reviewed.
- The key is the existing `[jev] key`, checked with `Jev.key_problem()`
  as the CVL `jev()` function does.

### 3. Wiring

- `MacieRun` reads `[macie] review` once. In `scan()`, for a reviewed
  identifier, each occurrence also goes to `ColumnFacts`. In
  `report()`, before the findings are stored, the reviewer runs.
- The review record goes to `_extra_data/macie/review.json` (beside
  `inputs.json`), in a group run.
- Docs: `docs/macie/review.md`, and the config keys in `results.md`.

## Decisions for David

Settled as proposed, all four (David, 2026-11-15).

1. **When Jev fails** (no key, network error, bad answer). The findings
   are complete either way. Proposed: the run is still valid; the
   review's status is `failed` with the reason, a `macie review: failed:
   ...` printout, an error in the error manager, and a log entry. The
   alternative is to fail the run, which would make an optional
   annotation able to block a compliance scan.
2. **Where the review sits.** Proposed: inside each detection, a list by
   column, as above; Macie's own fields unchanged. The alternative is a
   separate `review` section at the top of `macie_findings`.
3. **Names in cells.** `mask_cell()` keeps words without digits, which
   gives Jev its context but sends a name that sits next to a value.
   Proposed for the first build: keep it, say so in the docs, and add a
   `review_mask_words = true` option later that masks capitalised words
   too, if road-testers ask.
4. **`review = all`**, to review every identifier. Proposed: not in the
   first build; listing identifiers keeps the review a deliberate
   choice.
