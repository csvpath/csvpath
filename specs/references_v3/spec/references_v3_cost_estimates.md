# References v3: cost estimates

Draft for David's approval, 2026-11-17. It turns `notes/v3 - part 2 - cost estimates.txt`
(David) and the rulings of 2026-11-15/17 (decision log) into the shape the code
will follow. Fan-out is not part of this; it comes after the v3 MVP.

## Purpose

Tell a person, a program or an agent, before a reference runs, roughly how much
work its `query()` and `resolve()` will do, and why. Customers: FlightPath Data
(a UI), FlightPath Generator (agents), and anyone calling the finders directly.

The estimate is cheap by rule: it reads at most one root ledger per datatype and
never lists a directory or opens a manifest (David, 2026-11-17). It reads the
ledger through the never-writing source read, not the manager properties. With
`[references] sql = on` its counts come from SQL. Its own dominant cost is
reading a large ledger.

## Worked examples

Scores use the default weights below. "query" and "resolve" are what each would
read; counts marked `<=` are upper bounds.

```
$orders.files.:last()                                         local
  score 1    query 1    resolve 1
  query:   1 named-file manifest
  resolve: 1 version file

$*.results.:all().*:valid(:true())                            S3; the corpus: 3 groups, 11 runs, 23 instances
  score 4    query 4    resolve 1
  query:   1 ledger + 11 run listings + 23 instance manifests
  why:     '*' over 3 named-results groups; '.*' lists each run and reads each
           instance's manifest; :valid() reads the instance manifests already read

$*.results.:all().*:valid(:true())                            S3; 9,000 runs, 18,900 instances
  score 9    query 9    resolve 1
  query:   1 ledger + 9,000 run listings + 18,900 instance manifests
  why:     the same shape over ~800x the runs; a date window would narrow it,
           e.g. :from(:date("2026-11-01"))

$acme.results.:having(:errors(:idchain("add[0]")))            S3; 200 runs, 800 instances
  score 7    query 7    resolve 1
  query:   1 ledger + 200 run listings + 800 instance manifests + <=800 errors.json
  why:     :having() by content reads candidates' errors.json during query; it
           stops at a run's first match, so 800 is the most

$*.results.:flatten():from(:yesterday(:hour(18))).*:errors()  S3; 60 runs, 240 instances in the window
  would raise at resolve: several whole files (compendium 5.3)
  query 6:  1 ledger + 60 run listings + 240 instance manifests
  why:     '.*:errors()' selects 240 errors.json files; resolve reads one file's
           content at a time, so resolve this one from query()'s results, or
           select records, e.g. :errors():idchain("...")

$acme.results.:flatten():yesterday().purchases:errors(:idchain("customer[0]id[0]"))
                                                              S3; 24 runs yesterday, 4 statements each
  score 5    query 5    resolve 4
  query:   1 ledger + 24 run listings + 96 instance manifests
  resolve: 24 errors.json
  why:     naming one statement (.purchases) still lists each run and reads all
           its instance manifests, to order them; :idchain() then reads one
           errors.json per run

$*.files.:type("csv") UNION $acme.results.:last().*:errors():idchain("add[0]")      local
  left:    score 1   query 1    resolve 1   (1 name listing + 4 named-file manifests; resolve 0)
  right:   score 1   query 1    resolve 1   (1 ledger + 1 run listing + 4 instance manifests;
                                             resolve 4 errors.json)
```

The last two are David's own examples from his note. An expression gives one
estimate per side, each complete on its own; the caller weighs them (David's
note: "a reference expression results in two fully separate estimates"). A
sub-expression gives a nested pair.

## The interface

```python
est = finder.estimate()          # ReferenceEstimate3, from any ReferenceFinder3

est.score            # int 1..MAX_SCORE: the bucket of query + resolve together
est.query_score      # int: query() alone
est.resolve_score    # int: what resolve() adds after query()
est.would_raise      # None, or why query() or resolve() would raise (e.g. 5.3)
est.reads            # [Read(part="query", kind="instance_manifest", count=23,
                     #       basis="exact", because=".*"), ...]
est.why              # ["'.*' lists each run and reads each instance's manifest", ...]
est.weights          # the weights used, and est.backend
est.to_dict()        # all of the above, JSON-ready (for MCP, the UI)
est.summary()        # the text above, for agents

ReferenceEstimate3.MAX_SCORE   # 10: callers read the maximum, never hard-code it

ex = expression.estimate()       # ExpressionEstimate3
ex.left, ex.right    # ReferenceEstimate3, or ExpressionEstimate3 for a sub-expression
ex.summary(), ex.to_dict()
```

Each part is its own attribute, so a UI can show the two part scores and the
breakdown, and an agent can take `summary()` (David, 2026-11-17). `resolve()`
runs `query()` first, so its total work is query plus resolve: that is why
`score` buckets the sum, and a caller that only queries reads `query_score`.

Read kinds are a fixed vocabulary: `ledger`, `name_listing`, `run_listing`,
`named_file_manifest`, `group_manifest`, `run_manifest`, `instance_manifest`,
`definition`, `errors_json`, `vars_json`, `meta_json`, `version_file`,
`data_file`. Each count's `basis` is `exact`, `upper_bound` or `estimate`, and
`because` names the part of the reference that causes it.

## The score

An integer from 1 (trivial) to `MAX_SCORE`, 10. It is a log-scale bucket of
weighted reads: score 1 is up to 10 weighted reads, and each step up is x4.

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
defaults are honest guesses, not measurements, and are labelled so in the docs.
A weight covers a read's hidden calls too: every read is an `exists()` check
first, a ledger read a directory check as well, and a name listing an
`isfile()` per entry.

| backend | file read | listing | SQL query |
|---|---|---|---|
| local | 1 | 1 | -- |
| sftp | 5 | 5 | -- |
| s3, azure, gcs | 10 | 20 | -- |
| `[references] sql = on` | (content files keep their backend weight) | -- | 2 |

Under `sql = on` the ledger, manifest and listing reads become SQL queries;
content files (errors.json, version and data files, definitions) still come
from the backend. Your note's cases (an expensive local-seeming file share,
cheap local S3-compatible storage) are what the setting is for. Calibrating on
real cloud backends is after the MVP, and would cost cloud spend, so it needs a
go.

## What the estimate counts

It walks the parsed reference the way `query()` dispatches, takes counts from
the root ledger, and applies these read factors (measured on main, 2026-11-17):

| in the reference | query reads | resolve reads |
|---|---|---|
| FILES/CSVPATHS literal root | that name's manifest | -- |
| `*`, `:regex()`, `:choice()` root | a name listing, then each name's manifest | -- |
| a ledger-set form (`$*...:manifest()...`, a status or lifecycle gate) | the ledger, plus every named-file or group manifest (the live index) | -- |
| RESULTS, any root | the ledger | -- |
| a RESULTS run result, or a name_one field gate (`:completed(:false())`) | 1 run manifest per candidate run, per gate | -- |
| any RESULTS name_three (`.*`, `.purchases`, `:all()`, a range) | per run in play: 1 run listing + every instance manifest (they are read to order the instances) | -- |
| an instance field gate (`:valid(:true())`) | none beyond the instance manifests | -- |
| a field read from the ledger (no value in the manifest) | the ledger again, per record | -- |
| `:having()` by content | `<=` 1 content file per candidate (it stops at a match) | -- |
| a `:definition()` gate or definition-field filter | 1 definition per entity | -- |
| a content accessor (`:errors()`, a version file, `:definition()`) | -- | 1 file per result |
| a value field (`.*:uuid()`) | -- | the instance manifests again (each call reads them afresh) |
| a date window, a range, a pointer | narrows the counts, from ledger timestamps | -- |

Counts and their basis:
- **exact:** names, the ledger's entries, instances per run (the results ledger
  has one entry per instance), and anything a window or pointer narrows;
- **upper bound:** runs (a run deleted without a ledger mark is still listed),
  and `:having()` content reads;
- **estimate:** what only a manifest would say: FILES live versus deleted
  versions, CSVPATHS statements per version, and template shapes beyond the
  ledger's `run_home` paths.

Versions are counted from the ledger by status: FILES leaves out failed
registrations, and CSVPATHS leaves out unchanged reloads. File sizes are not
modelled: a large version file counts as one read.

## Where it shows up

- `ReferenceFinder3.estimate()` and `ReferenceExpression3.estimate()`. (David's
  sketch called it `find_cost()`.)
- A CLI item, "estimate a reference", beside "check SQL coverage".

## Not in the MVP

- Fan-out, and anything that splits a reference (after the MVP, for the next
  FlightPath release).
- Calibrated or learned weights.
- File sizes.
- Lowering the reads themselves (e.g. ordering instances without reading every
  manifest, or memoising run manifests); the estimate reports today's costs.
