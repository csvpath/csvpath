# Reviewing findings with Jev

An optional step after a file is scanned: [Jev](https://docs.typesafe.ai)
reads the context of each group of findings and says how likely they are
to be real. It does not change the findings. Every count, severity and
cell stays as the rules found it; the review is added beside them, so a
reviewer can start with what Jev doubts.

It is off unless you turn it on, and only for the identifiers you name.

Naming `NAME` or `ADDRESS` does something different: Jev checks the file's
columns for those identifiers, which Macie finds with machine learning
and rules cannot. See [NAME and ADDRESS](#name-and-address) below.

## Turning it on

```ini
[macie]
review = USA_SOCIAL_SECURITY_NUMBER, CREDIT_CARD_NUMBER
review_model = jev-1.14.0
review_max_questions = 50
review_threshold = 0.7

[jev]
key = JEV_KEY
```

- **`review`**: the identifiers to review, managed or custom, by name.
  There is no `all`: reviewing is a choice made per identifier.
- **`review_model`**: the Jev model, pinned so that runs can be compared
  (default `jev-1.14.0`; `jev-latest` is refused).
- **`review_max_questions`**: at most this many questions per file
  (default 50); the rest are listed as not reviewed.
- **`review_threshold`**: for NAME and ADDRESS only, how likely Jev must
  say a column is before it counts (default 0.7).
- **`[jev] key`**: your Jev key, as for the CVL `jev()` function. Keep it
  in an environment variable and name the variable here.

## What Jev is told

One question per file, identifier and column, all in one request after
the file's last line. **No value is sent.** In every word that holds a
digit, each letter becomes `A` and each digit `#`, so `309-04-7794` is
sent as `###-##-####`. Jev is told:

- the identifier, the file name, the column names, and the flagged
  column;
- how many rows were flagged, and how many distinct values;
- facts the scan computed, in plain words: "Every one of the 400 flagged
  values is the same value.", "Only 9 distinct values among 1400 flagged
  cells", "The flagged values are consecutive";
- why the scan flagged them (a keyword in the column header, or near the
  value);
- up to three masked samples of the flagged cells, e.g.
  `ssn on file: ###-##-####`.

**Words without digits are sent as written**, because they are the
context: "gift card shipment, tracking ####..." is what tells a tracking
number from a card number. That includes a name written next to a value.
If your cells hold names beside the values you review, consider that
before turning the review on.

## What you get

On the `macie` print stream, a line per question and a summary:

```
macie review USA_SOCIAL_SECURITY_NUMBER column 7 ref_no: unrelated (0.06); Every one of the 4000 flagged values is the same value.
macie review USA_SOCIAL_SECURITY_NUMBER column 3 ssn: likely (0.91); Every flagged value is different.
macie review: complete, 2 questions, jev-1.14.0, 0.4 s, 512 tokens in, 61 out
```

In `macie_findings`, each reviewed detection gains a `review` list, one
entry per column:

```json
"review": [
  {
    "column": 7,
    "columnName": "ref_no",
    "verdict": "unrelated",
    "confidence": 0.06,
    "probabilities": {"likely": 0.06, "doubtful": 0.21, "unrelated": 0.73},
    "facts": ["Every one of the 4000 flagged values is the same value."]
  }
]
```

- **`verdict`**: `likely` (very probably real), `doubtful` (probably
  not), or `unrelated` (a false alarm: ids, codes, placeholders).
- **`confidence`**: Jev's probability that the values are real.

The `csvpath` section gains a `review` summary: `status` (`complete`,
`partial` when `review_max_questions` cut it short, or `failed`),
`reason`, `model`, `questions`, tokens, seconds, and `not_reviewed`.

In a named-paths group run, the run's `_extra_data/macie/` also holds
`review.<csvpath>.json`: the exact request (masked) and Jev's response,
so the review can be audited. A standalone run prints and stores the
variable only.

## When the review cannot be done

No key, a network error, or an answer Jev should not give: the review's
status is `failed`, with the reason, on the print stream (`macie review:
failed: ...`), in the run's errors, and in the log. **The run stays
valid**: the findings are complete without the review.

## How well it works

In two experiments on 30 labelled cases
(`specs/macie/jev-experiment-2026-11-15.md`), Jev with these questions
put 29 of 30 in the right verdict, for about 275 tokens a question and
well under a second per file. The one it got wrong was nine
phone-shaped product codes repeated across 1,400 rows. Treat a verdict
as a ranking for a person to check, not a decision.

## NAME and ADDRESS

Macie finds full names (`NAME`) and postal addresses (`ADDRESS`) with
machine learning. A wrapper that selects them is converted to
`macie_jev.nocontrib("NAME")` and `macie_jev.nocontrib("ADDRESS")`. They
are checked only when `[macie] review` names them:

```ini
[macie]
review = NAME, ADDRESS
```

**One question per column**, all in one request after the file's last
line. **No value and no word is sent.** Each upper-case letter becomes
`A`, each lower-case letter `a` and each digit `#`, so `Akua Mansa` is
sent as `Aaaa Aaaaa` and `12 Main St, Springfield, IL 62704` as
`## Aaaa Aa, Aaaaaaaaaaa, AA #####`. Jev is told the column's header, the
file's other headers, how many rows are filled and distinct, and the
most common shapes with their counts. An ADDRESS question is asked only
of a column whose shapes hold a postal code after a space or a comma, so
a street, a city or a ZIP code alone costs nothing.

**What you get is ours, not Macie's.** A column counts when Jev's
probability that it holds the data is at least `review_threshold`, and
then every filled cell in it is counted. The results are a separate
`jev` section of `macie_findings`, never mixed into `sensitiveData`:

```json
"jev": {
  "detectedBy": "jev",
  "status": "complete",
  "model": "jev-1.14.0",
  "threshold": 0.7,
  "questions": 5,
  "totalCount": 7,
  "detections": [
    {"type": "NAME", "count": 4,
     "columns": [{"column": 2, "columnName": "full_name", "count": 4,
                  "verdict": "likely", "confidence": 0.95}]}
  ],
  "not_checked": [],
  "not_asked": [{"identifier": "ADDRESS", "column": 2,
                 "columnName": "full_name",
                 "reason": "no postal code in the column's shapes"}]
}
```

The print stream has a line for each column found
(`macie jev NAME column 2 full_name: 4 cells (likely, 0.95)`) and a
summary. The request and the answers are recorded in the run's
`_extra_data/macie/jev.<csvpath>.json`.

**When it is not done.** If `[macie] review` does not name an identifier,
its status is `off` and the stream says it is not checked. If Jev cannot
be reached or the key is missing, the status is `failed`, NAME and
ADDRESS are listed as not checked, with the reason, on the stream and in
the run's errors. **The run stays valid.** Do not read an empty `jev`
section as "no names here" unless its status is `complete`.

**What it misses.** Names inside free text, such as a notes column with
"spoke to Akua Mansa", are not found: the question is about a column,
and words are never sent. A column holding names and something else is
judged as one. First names alone are not full names, as for Macie.

**How well it works.** In the experiment
(`specs/macie/jev-names-experiment-2026-11-18.md`), 32 synthetic columns
asked about both identifiers: every true column scored at least 0.78,
and every look-alike (product names, companies, cities, streets with no
postal code, ZIP codes, GPS, dates, phones) at most 0.61, so all 60 were
right at 0.7. About 300 tokens a question; the cost grows with columns,
not rows. The columns were tidy; real ones are messier, so treat the
results as a strong lead for a person to check.
