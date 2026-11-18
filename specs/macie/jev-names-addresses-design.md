# NAME and ADDRESS through Jev: design note

Draft, 2026-11-18. For David to react to before any code or experiment.

## The idea

Macie finds `NAME` (full names, Latin characters only) and `ADDRESS` (a
city or place with its postal code, in Australia, Canada, France,
Germany, Italy, Spain, the UK and the US) with machine learning. Rules
cannot do this, so today both are reported as not translated
(`limitations.md`). Jev can judge them. That gives an answer to Macie on
an important check, and a ready reply when someone objects "but you
can't find names".

The answer would be **ours, not Macie's** (fidelity C): a different
model, with different misses.

## How it differs from the review we have

The review we have (`jev-review-build.md`) asks about cells that a rule
has already flagged. It masks the values, and it only annotates. For
NAME and ADDRESS, no rule flags anything, so two of the review's
foundations change:

1. **Jev finds; it does not only annotate.** Its answer becomes the
   finding. The rule that the review "never removes" still holds,
   because nothing is removed, but these findings come from a model's
   judgment, not from a rule. Each one has to say so.
2. **Masking hides the very thing asked about.** Our mask keeps words
   without digits, so names would be sent as written (review decision
   3). For a NAME check that means sending the sensitive data itself.

## Proposal: judge columns, not cells, from masked shapes

There is one question per column, for each of NAME and ADDRESS. Values
are masked with a mask that keeps case. This is a new mask, alongside
today's:

| Value | Today's mask | Case-keeping mask |
|---|---|---|
| `Akua Mansa` | `Akua Mansa` (no digit, kept) | `Aaaa Aaaaa` |
| `12 Main St, Springfield, IL 62704` | `## Main St, Springfield, IL #####` | `## Aaaa Aa, Aaaaaaaaaaa, AA #####` |
| `akua@acme.com` | kept | `aaaa@aaaa.aaa` |

The case-keeping mask leaves only shape, case and punctuation; no word
leaves the machine. The question also gets the column header, its
neighbours, and the column facts we already compute (distinct values,
how many rows are filled).

**Worked example.** `employees.csv` has the columns `row_id`,
`full_name`, `employee_id`, `manager_note` and `email`:

```
Identifier: NAME (a person's full name).
Column: full_name. Neighbours: row_id, employee_id, manager_note.
1,000 rows, 998 filled, 991 distinct.
Shapes (masked, case kept): Aaaa Aaaaa (612), Aaaaa Aaaaaaa (240),
Aa Aaa (41), Aaaa A. Aaaaa (37), ...
Does this column hold people's full names?
```

`choice()` answers likely, doubtful or unrelated, with a probability.
For "likely" at or above the threshold, **each filled cell in the column
is an occurrence** of NAME, reported as Macie reports them, with
`"detectedBy": "jev"`, the verdict and the confidence on the detection:

```json
{"type": "NAME", "count": 998, "detectedBy": "jev",
 "review": {"verdict": "likely", "confidence": 0.94, "model": "jev-1.14.0"},
 "occurrences": {"cells": [{"column": 2, "columnName": "full_name", "row": 2}, ...]}}
```

For ADDRESS, a postal code rule (`#####`, `A#A #A#`, and the UK's
outward and inward codes) could screen columns before Jev is asked, so
only columns that may hold addresses cost a question.

## What it misses

- **Names inside free text** (`manager_note`: "spoke to Akua Mansa
  today"). A column-level question about a notes column says "unrelated",
  and Macie would find the name. A cell-level question could find it,
  but only by sending each cell's words, which is option B below.
- **Mixed columns**, such as a `contact` column holding names and email
  addresses. The whole column is judged as one.
- **Accuracy** is unknown until we run an experiment. The SSN review was
  right 29 times in 30 with masked facts, but that was a judgment about
  values a rule had found. This is detection from shape alone.

## Option B, an explicit opt-in: send cell text

`review_send_values = NAME, ADDRESS` would send each cell's words, so
Jev can find names in free text, one batch of cells per question. That
breaks review rule 2 (values are masked), so it would only ever be a
separate, explicit opt-in, documented as such. It is also where the cost
grows with the file.

## Cost

These rates come from the review experiments: about 250 to 300 tokens a
question, and about $0.01 per 43,000 tokens.

| Shape | Questions | Tokens | Cost |
|---|---|---|---|
| Column level, 40 columns, both identifiers | 80 | ~24,000 | well under a cent |
| Column level, 1,000 files of 40 columns | 80,000 | ~24M | ~$5.60 |
| Option B, 1M rows, 50 cells a question, one text column | 20,000 | ~20M+ | several dollars a file |

Column level does not grow with rows, only with columns and files.
Option B grows with rows. It would need a cap, like
`review_max_questions` today, and sampling, as Macie's automated
discovery samples.

## Failure

If Jev cannot be reached, or the key is missing, NAME and ADDRESS are
**not checked**, and the run says so loudly. Findings with those
identifiers missing must not read as "no names here". The run stays
valid, as for the review, unless David decides a check that cannot run
should fail the run.

## Steps

1. **An experiment, with your OK** (cents, as before). Take about 30
   columns: names, addresses, and look-alikes such as product names,
   cities without postal codes, company names, and notes with and
   without names. Ask the column question with the case-keeping mask.
   Is it right often enough?
2. If it is: the converter translates NAME and ADDRESS when
   `[macie] review` names them, the run asks after the scan, the
   findings are marked `detectedBy: jev`, and the docs say what is
   missed.
3. Option B only if testers ask for it.

## Decisions for David

1. Are findings from Jev acceptable in `macie_findings`, marked
   `detectedBy: jev`, or should they be kept in a separate section?
2. Is the case-keeping mask acceptable to send? It keeps shape and case,
   with no words.
3. Run the experiment (step 1)?
4. If Jev fails: NAME and ADDRESS "not checked", run valid. Or should
   the run fail?
