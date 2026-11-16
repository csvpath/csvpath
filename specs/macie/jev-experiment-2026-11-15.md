# Jev review experiment, 2026-11-15

The experiment from `specs/macie/jev-review-design.md`: can Jev, given
only masked context, tell real findings from false ones? Script:
`tests/macie/live/jev_review_experiment.py`. 29 synthetic cases, each a
column of findings labelled with the truth: 14 real, 12 false, 3
ambiguous (not scored).

## Cost and speed

| Run | Requests | Questions | Tokens in | Tokens out | Time | Balance |
|---|---|---|---|---|---|---|
| Pilot | 1 | 3 | 796 | 58 | 0.17 s | $4.99, unchanged |
| Full | 4 | 39 | 7,807 | 955 | 0.63 s | (to read) |

About 200 tokens in and 25 out per question. `jev-latest` resolved to
`jev-1.14.0` in every request. Building the CVL Jev functions cost about
a cent in all (David). At these sizes, cost is not what limits the
feature.

## How well it separates

`noul()`, the probability that the flagged values are real:

| Real | p | | False | p |
|---|---|---|---|---|
| dob-patients | 0.93 | | phone-sku | 0.69 |
| phone-contacts | 0.92 | | ssn-placeholder | 0.66 |
| ssn-hr | 0.86 | | dob-flags | 0.62 |
| dl-hr | 0.81 | | passport-photo | 0.55 |
| card-pay | 0.78 | | bank-crm | 0.50 |
| npi-providers | 0.76 | | nhs-supplier | 0.38 |
| aws-config | 0.69 | | dl-download | 0.38 |
| passport-travel | 0.68 | | card-tracking | 0.22 |
| cpf-br | 0.65 | | card-library | 0.19 |
| ssn-note | 0.64 | | ssn-ticket | 0.17 |
| nhs-patients | 0.62 | | aws-docs | 0.17 |
| cf-payroll | 0.54 | | cpf-invoice | 0.12 |
| dni-es | 0.47 | | | |
| iban-note | 0.44 | | | |

- **AUC 0.869**: a real case outranks a false one 87% of the time.
- Mean 0.70 for real, 0.39 for false. At a single 0.5 cut, 19 of 26 are
  right.
- **With the design note's three bands** (`likely` at 0.7 or more,
  `doubtful` at 0.3 or less, `uncertain` between), **none of the 26 is
  in the wrong band**: 6 real cases are `likely`, 5 false ones are
  `doubtful`, and 15 are `uncertain`. A verdict that commits is right
  every time here; 11 of 26 commit.

Ambiguous cases: vendors' support phone lines 0.86 (Jev treats them as
real phone numbers, which they are), dogs' dates of birth 0.49, an "SSN
ending in" note with the full number in it 0.27 (wrong: the full number
is there).

## What it gets right, and what it misses

**Right: context in the words.** Every false case with telling words
scored low: SSN-shaped ticket numbers (0.17), "gift card shipment,
tracking" (0.22), a library card column (0.19), the AWS documentation
example key (0.17), CPF-shaped invoice numbers (0.12).

**Missed: facts about the column.** The false cases that scored high
are the ones only the numbers give away:

- `ssn-placeholder` (0.66): one distinct value in 400 rows, `123-45-6789`.
- `dob-flags` (0.62): one distinct value in 40 rows, `1900-01-01`.
- `phone-sku` (0.69): 9 distinct values in 1,400 rows.
- `passport-photo` (0.55): sequential ids.

The question stated the counts ("400 of 400 rows; 1 distinct flagged
value") but Jev did not weigh them. Those signals are cheap and exact in
our own code, so they need not be Jev's job: either say them plainly
("every one of the 400 rows holds the same value"), or compute them
ourselves and report them beside Jev's verdict.

**Real cases with low scores** were the ones with the least context:
`iban-note` (0.44, two masked IBANs in supplier notes) and `dni-es`
(0.47, a `dni` column). An IBAN masks to letters and digits only, so
little is left to judge.

## `choice()` against `noul()`

The 10 `choice()` cases were, by an oversight, all real. All 10 came back
`likely`, including `iban-note`, which `noul()` scored 0.44; the
`likely` probabilities track the `noul()` scores closely. No conclusion
on false cases; a second run should ask `choice()` across both labels.

## What this suggests

1. **The feature is practical.** Cheap, fast, and with three bands its
   committed verdicts were all right.
2. **Column facts are ours to compute**, not Jev's: all values the same,
   very few distinct values, sequential values. Put them in the
   question in plain words, and add them to the review as our own
   signals.
3. **A second run** (cents): the plain-words column facts, `choice()` on
   real and false cases alike, and a few more cases with little context,
   to see whether the `uncertain` band shrinks.

## The second run

The same 29 cases plus 4 with little context (`ssn-bare`,
`iban-payroll`, `ssn-testdata`, `card-game`), with two changes
(`--run 2`):

- **Column facts in plain words**, computed by our code from the counts:
  "Every one of the 400 flagged values is the same value."; "Only 9
  distinct values among 1400 flagged cells: the same few values
  repeat."; "Every flagged value is different."; and, where our code
  would see it, "The flagged values are consecutive".
- **`choice()` on every case**, real and false alike, as well as
  `noul()`.

| | First run | Second run |
|---|---|---|
| Questions | 39 | 66 |
| Tokens in / out | 7,807 / 955 | 16,194 / 2,023 |
| Time | 0.63 s | 0.85 s (8 requests) |
| `noul()` AUC | 0.869 | **0.980** |
| `noul()` right at 0.5 | 19 of 26 | 27 of 30 |
| `noul()` committed (three bands), wrong | 11 of 26, 0 wrong | **19 of 30, 0 wrong** |
| `choice()` AUC (on p(likely)) | (real cases only) | **0.996** |
| `choice()` right (likely = real) | (real cases only) | **29 of 30** |

**The column facts fixed the cases Jev had missed:** the placeholder SSN
went from 0.66 to 0.24, the `1900-01-01` default from 0.62 to 0.27, the
consecutive photo ids from 0.55 to 0.25. The one left is `phone-sku`
(9 distinct SKUs in 1,400 rows): 0.59 by `noul()`, and the only case
`choice()` got wrong (`likely`, at 0.52).

**`choice()` is the better question.** Its three answers are the
review's verdicts, and its p(likely) separates almost perfectly. It also
said more about the ambiguous cases: dogs' dates of birth `doubtful`,
vendors' support lines `likely`, and the "SSN ending in" note
`unrelated` (wrong: the full number is in the note too).

**Weakest real cases** are still the ones with least context:
`iban-note` (0.49 / 0.50) and `dni-es` (0.53 / 0.59). They come out
right under `choice()`, but only just.

**Cost:** 18,000 tokens in total for the second run, about 275 a
question with the facts. The $4.99 balance had not moved after the first
run; David's earlier figure is $0.01 for about 43,000 tokens.

## Conclusions

1. **Build it.** Masked context plus our own column facts, asked as a
   `choice()`, gets 29 of 30 right, in under a second for a whole run,
   for a fraction of a cent.
2. **The column facts are ours**: same value throughout, few distinct
   values, consecutive values. Compute them exactly and state them in
   the question; record them in the review beside Jev's verdict.
3. **Use `choice()`** with `likely`, `doubtful`, `unrelated` as the
   verdicts, and p(likely) as the confidence.
4. **Still annotate, never remove.** One case in 30 was wrong, and the
   ambiguous ones need a person.
