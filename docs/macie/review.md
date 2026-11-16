# Reviewing findings with Jev

An optional step after a file is scanned: [Jev](https://docs.typesafe.ai)
reads the context of each group of findings and says how likely they are
to be real. It does not change the findings. Every count, severity and
cell stays as the rules found it; the review is added beside them, so a
reviewer can start with what Jev doubts.

It is off unless you turn it on, and only for the identifiers you name.

## Turning it on

```ini
[macie]
review = USA_SOCIAL_SECURITY_NUMBER, CREDIT_CARD_NUMBER
review_model = jev-1.14.0
review_max_questions = 50

[jev]
key = JEV_KEY
```

- **`review`**: the identifiers to review, managed or custom, by name.
  There is no `all`: reviewing is a choice made per identifier.
- **`review_model`**: the Jev model, pinned so that runs can be compared
  (default `jev-1.14.0`; `jev-latest` is refused).
- **`review_max_questions`**: at most this many questions per file
  (default 50); the rest are listed as not reviewed.
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
