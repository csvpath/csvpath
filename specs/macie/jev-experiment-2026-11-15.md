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
