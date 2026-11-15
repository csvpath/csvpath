# Jev review of Macie findings: design note

Draft, 2026-11-15. For David to react to before any code.

## The idea

An optional review step: Jev is asked about each group of findings and
answers how likely they are to be real. It closes part of the gap
between our rule-based stand-ins and Macie, which also uses machine
learning (for `NAME` and `ADDRESS`, and very likely for context), and it
gives a reviewer a ranked list instead of a flat one.

Three rules shape everything below:

1. **The review annotates; it never removes.** Counts, severities, cells,
   errors and printouts stay exactly what the rules produce, because
   Macie support fails loudly (legal stakes). The review is a separate
   field next to each detection.
2. **Values are masked.** A sensitive data scan exists to keep values
   from going where they should not. Jev is sent the context of a
   finding, not the value. Sending values would be a separate, explicit
   opt-in, if ever.
3. **Off unless asked for**, and then only for the identifiers named.

## What Jev is asked

One question per **file, column and identifier**, not per cell. Findings
cluster: a `ref_no` column of 4,000 SSN-shaped values is one judgment,
not 4,000. That caps the calls per file at the number of columns with
findings, times the identifiers reviewed.

### The mask

Every letter becomes `A` and every digit `#`, the notation
`FormatDetector` already uses. Spaces and punctuation are kept. The
request tells Jev the notation.

| Value | Masked |
|---|---|
| `309-04-7794` | `###-##-####` |
| `RSSMRA85T10A562S` | `AAAAAA##A##A###A` |
| `+1 (212) 555-0148` | `+# (###) ###-####` |
| `EMP-123456` | `AAA-######` |

The words around a value in the same cell are kept, with any other
value-shaped text in them masked the same way. For example:
`call +# (###) ###-#### after 5pm`.

### An example request

A file `orders.csv` has 4,000 `USA_SOCIAL_SECURITY_NUMBER` occurrences
in a column `ref_no` (the header keyword was not what fired: a keyword
in the `notes` column did, on 12 rows).

**State** (the context, sent once per file):

```
A data-loss-prevention scan of a CSV file flagged values that may be
sensitive. Values are masked: each letter is A, each digit is #,
punctuation and spaces are kept. You are told the column, the shape,
nearby words, and facts about the column; never the values.

File: orders.csv, 41 columns, 4,000 data rows.
```

**Question** (one per file, column and identifier), as a `noul()`:

```
Identifier: USA_SOCIAL_SECURITY_NUMBER (a US Social Security number).
Column: ref_no. Column header neighbours: order_id, customer_id, sku,
ref_no, ship_date.
Occurrences: 4,000 of 4,000 rows; 4,000 distinct values; all have the
shape ###-##-####.
Why the scan flagged them: the keyword "ssn" appeared within 30
characters in the notes column on 12 rows.
Samples of the cell text around an occurrence (masked):
  "###-##-####"   (15 samples, all the same)
Notes column samples near the keyword (masked):
  "ssn verified for order AAA-######"
  "customer ssn on file, ref ###-##-####"

Is it likely that the ref_no column holds real US Social Security
numbers?
```

**Answer**: a probability, which becomes the review:

```json
"review": {
  "verdict": "doubtful",
  "confidence": 0.18,
  "model": "<the pinned Jev model>",
  "question_id": "orders.csv:ref_no:USA_SOCIAL_SECURITY_NUMBER"
}
```

`verdict` is from thresholds in config: `likely` at or above 0.7,
`doubtful` at or below 0.3, `uncertain` between. The thresholds are
ours to tune in the experiment.

`choice()` (likely, doubtful, unrelated) is the alternative to `noul()`;
the experiment tries both.

## Where it lives

- **After the file, not in-line.** One batched request per file, after
  the last line, using Jev's several-questions-in-one-request form. In-line
  review would add a round trip to matching lines and buys nothing until
  the review is allowed to change the run's flow, which rule 1 rules out.
- **Config** (`config.ini [macie]`, or the project rulesbase):

  ```ini
  [macie]
  review = BRAZIL_RG_NUMBER, SPAIN_SOCIAL_SECURITY_NUMBER
  review_max_questions = 50
  review_model = <a pinned Jev model, never jev-latest>
  ```

  `review_max_questions` is a circuit breaker per run, like
  `max_findings`. When it trips, the rest are left unreviewed and the
  printouts say so.
- **The record.** In a named-paths group run, the exact requests and
  responses go to `_extra_data/macie/review.json` beside the run's other
  Macie inputs, with the model and the token usage the API reports. An
  auditor sees what was asked and what came back. The model is pinned,
  never `jev-latest`.
- **Printouts** add one line per reviewed detection, e.g.
  `macie USA_SOCIAL_SECURITY_NUMBER ref_no: review doubtful (0.18)`.

## What we do not know yet

- **Whether masked context is enough** for Jev to separate real findings
  from false ones. That is the experiment's question.
- **Cost per question.** The API reports tokens, not dollars, so cost is
  read off the account balance before and after each experiment. The
  benchmark is the $5 now on the account (David, 2026-11-15).
- **Latency** per batched request.
- **Jev's data handling** (retention, training use). Masking makes this
  matter less, not nothing: column names and nearby words go to Jev.

## The experiment (before any of the above is built)

A script outside the package, in `tests/macie/live/`, with David's OK
for each run:

1. **Cases.** About 30, each labelled with the truth:
   - our known false positives against Macie from the live check and
     probes (the seven German IDs; the keyword-inside-a-word rows, as
     they would have been reported before 2026-11-15);
   - synthetic false positives: SSN-shaped order numbers, dates in
     shipping columns, card-shaped tracking numbers, CPF-shaped invoice
     ids;
   - true positives: the same shapes in columns and contexts where they
     are real.
2. **One request** per case group, masked as above; `noul()` and
   `choice()` both tried on a subset.
3. **Measured:** how well the probabilities separate the labels, the
   tokens and the balance change, and the time per request.
4. **Before running:** David sees the questions and the number of calls.
   The key is read from `~/dev/exports.sh` (`JEV_KEY` only) inside the
   one command that needs it; it is never printed or written.

If masked context separates the cases well for a few cents, we design
the feature in detail. If not, we know cheaply.

## Tests, when it is built

Jev is mocked: `TypeSafeClient` takes an `httpx` transport, so tests
pass a mock transport and never reach the API. (The existing CVL Jev
tests call the live API and fail without a key; they should get the same
treatment.)
