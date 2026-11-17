# References v3: cost estimates

Draft for David's approval, 2026-11-17. It turns `notes/v3 - part 2 - cost estimates.txt`
(David) and the rulings of 2026-11-15/17 (decision log) into the shape the code
will follow. Fan-out is not part of this; it comes after the v3 MVP.

## Purpose

Tell a person, a program or an agent, before a reference runs, roughly how much
work its `query()` and `resolve()` will do, and why. Customers: FlightPath Data
(a UI), FlightPath Generator (agents), and anyone calling the finders directly.

The estimate is cheap by rule: it reads at most one root ledger per datatype,
plus a named-paths group's definition for its statement count, and it never
lists a directory (David, 2026-11-17). With `[references] sql = on` the counts
come from SQL.

## Worked examples

Scores use the default weights below. The counts are what each reference's
query and resolve would read.

```
$orders.files.:last()                                  local
  score 1      query 1   resolve 1
  query:   1 manifest                      resolve: 1 version file
  why:     one named-file, one manifest

$*.results.:all().*:valid(:true())                     S3, 23 runs / 92 instances
  score 5      query 5   resolve 1
  query:   1 ledger + 23 listings + 92 instance manifests
  resolve: 0
  why:     '*' over every named-results group (3); '.*' reads each instance's
           manifest; :valid() is a field gate, no extra file

$*.results.:all().*:valid(:true())                     S3, 9,000 runs / 36,000 instances
  score 9      query 9   resolve 1
  query:   1 ledger + 9,000 listings + 36,000 instance manifests
  why:     the same shape over 400x the runs -- a date window would narrow it,
           e.g. :from(:date("2026-11-01"))

$acme.results.:having(:errors(:idchain("add[0]")))     S3, 200 runs / 800 instances
  score 7      query 7   resolve 1
  query:   1 ledger + 200 listings + 800 instance manifests + 800 errors.json
  why:     :having() by content reads every candidate's errors.json during query

$*.files.:type("csv") UNION $acme.results.:last().*:errors():idchain("add[0]")      local
  left:    score 1   query 1 listing + 4 manifests        resolve 0
  right:   score 1   query 1 ledger + 1 listing + 4 manifests
                     resolve 4 errors.json
```

An expression gives one estimate per side, each complete on its own; the caller
weighs them (David's note: "a reference expression results in two fully
separate estimates"). A sub-expression gives a nested pair.

## The interface

```python
est = finder.estimate()          # ReferenceEstimate3, from any ReferenceFinder3

est.score            # int 1-10: the larger of the two part scores
est.query_score      # int 1-10
est.resolve_score    # int 1-10
est.query_reads      # {"ledger": 1, "listings": 23, "manifests": 92}
est.resolve_reads    # {}
est.why              # ["'*' over every named-results group (3)", ...]
est.estimated        # what was estimated rather than counted, e.g.
                     # ["instances per run: from the group's 4 statements"]
est.summary()        # the text above, for agents

ex = expression.estimate()       # ExpressionEstimate3
ex.left, ex.right    # ReferenceEstimate3, or ExpressionEstimate3 for a sub-expression
ex.summary()
```

Each part is its own attribute, so a UI can show the two part scores and the
breakdown, and an agent can take `summary()` (David, 2026-11-17).

## The score

An integer from 1 (trivial) to 10 (the maximum v3 gives). It is a log-scale
bucket of weighted reads: score 1 is up to 10 weighted reads, and each step up
is x4.

| score | weighted reads up to |
|---|---|
| 1 | 10 |
| 2 | 40 |
| 3 | 160 |
| 4 | 640 |
| 5 | 2,560 |
| 6 | 10,240 |
| 7 | 40,960 |
| 8 | 163,840 |
| 9 | 655,360 |
| 10 | more |

Weighted reads = sum over reads of (count x weight). A part with no reads
scores 1. The score is ordinal: higher means more work, roughly x4 per step. It
is not a time. A caller sets its own thresholds, e.g. Generator might use one
agent up to 4 and several above 7.

## Weights

Per read kind and backend, configurable as `[references] cost_weights`. The
defaults are honest guesses, not measurements, and are labelled so in the docs:

| backend | file read | listing |
|---|---|---|
| local | 1 | 1 |
| sftp | 5 | 5 |
| s3, azure, gcs | 10 | 20 |

Your note's cases (an expensive local-seeming file share, cheap local
S3-compatible storage) are what the setting is for. Calibrating on real cloud
backends is after the MVP, and would cost cloud spend, so it needs a go.

## What the estimate counts

It walks the parsed reference the way `query()` dispatches, takes counts from
the root ledger, and applies a read factor per function:

| in the reference | query reads | resolve reads |
|---|---|---|
| a literal root | that name's manifest (FILES, CSVPATHS) or its runs (RESULTS) | -- |
| `*`, `:regex()`, `:choice()` root | the names in play, from the ledger | -- |
| a RESULTS run in play | 1 listing | -- |
| `.*`, `:all()`, a range in name_three | 1 instance manifest per instance in play | -- |
| a field gate (`:valid(:true())`, `:type("csv")`) | none extra | -- |
| `:having()` by content | 1 content file per candidate | -- |
| a content accessor (`:errors()`, a version file, `:definition()`) | -- | 1 file per result |
| a date window, a range, a pointer | narrows the counts, from ledger timestamps | -- |

Counted, not estimated: names, versions, runs, and instances per run (the
results ledger has one entry per instance), and anything a window or pointer
narrows. Estimated, and marked in `est.estimated`: what the ledger cannot tell,
e.g. live versus deleted where only a manifest would say, statements per
version, and template shapes beyond the ledger's `run_home` paths. File sizes
are not modelled: a large version file counts as one read.

## Where it shows up

- `ReferenceFinder3.estimate()` and `ReferenceExpression3.estimate()`.
- A CLI item, "estimate a reference", beside "check SQL coverage".

## Not in the MVP

- Fan-out, and anything that splits a reference (after the MVP, for the next
  FlightPath release).
- Calibrated or learned weights.
- File sizes.
