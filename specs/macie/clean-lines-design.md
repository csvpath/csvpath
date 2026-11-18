# Clean lines: a Macie csvpath that collects the lines without findings

Draft, 2026-11-18. For David to react to before any code.

## The question

A csvpath after a Macie csvpath, with `source-mode: preceding`, reads
the Macie csvpath's collected lines. Today those are the lines with
findings (worklist, "Design questions to revisit"). Could the Macie
csvpath collect the clean lines instead, so the next csvpath gets only
lines with nothing sensitive in them?

## It already works, with one mode

`return-mode: no-matches` makes a csvpath collect the lines it does not
match. A Macie csvpath matches a line when an identifier finds
something on it, so with that mode it collects exactly the clean lines.
No Macie code is involved: the functions, the tally, the errors and the
report do not depend on what is collected.

Tried on 2026-11-18 with pair 21 (driver's licenses, 10 data lines, 9
with findings). The group had the Macie csvpath and then
`~ source-mode: preceding id: after ~ $[*][ yes() ]`:

| Macie csvpath | Its lines | `after` reads | Findings | Errors |
|---|---|---|---|---|
| as generated | 1 to 9 | 1 to 9 | 12 | 12 |
| with `return-mode: no-matches` | 10 | 10 | 12 | 12 |

The findings, errors and printouts are the same either way.

## What a build would add

1. **A way to ask for it.** `[macie] collect = clean` in config.ini, or
   `findings`, the default. Like the limits, it is read when the group is
   loaded. The converter writes `return-mode: no-matches` and
   `macie-collect: clean` into the csvpath, so the run dir records which
   kind of lines a run collected. A converter argument would do the same
   for standalone conversions.
2. **The breaker must be loud.** When the breaker trips, the file stops
   and the lines after it are never scanned. In clean mode they are also
   never collected, so the next csvpath silently gets a short file. Tried
   with pair 03 (6 lines, `max_findings 5`, which trips on line 4): the
   clean lines are line 3 only, and lines 5 and 6 are gone. The run is
   still valid. Proposed: in clean mode a tripped breaker makes the run
   invalid and prints
   `macie: breaker tripped at line 4; lines after it were not scanned and are not among the clean lines`.
   (In findings mode the run stays as it is today.)
3. **Say what clean means.** Clean means no finding by the identifiers
   that were translated. `NAME` and `ADDRESS` are not translated, nor is
   any identifier the conversion report lists as skipped. So a run in
   clean mode prints, once:
   `macie: clean lines are checked for 31 identifiers; not checked: NAME, ADDRESS`
   (the count is the wrapper's).
4. **Tests:** pairs 21 and 03 in both modes, the config key, the metadata,
   the breaker rule, the printout. **Docs:** a section in
   `docs/macie/results.md`.

About a day. Nothing in core changes: `return-mode` and `source-mode`
are existing modes.

## Uses

- **Pass on what is safe.** A pipeline sends only clean lines on to a
  less trusted stage, such as a vendor feed, analytics or an LLM. The
  findings, with their rows, are the record of what was held back.
- **Redaction review.** The findings name the held-back rows, and the
  clean lines are the rest.

## Recommendation

Build it before the first release if you want it as a talking point.
It is small, and it is a natural answer to "what do I do with the
results?" Otherwise it can safely wait: nothing else depends on it.

## Decisions for David

1. Build now, or after the first release?
2. Is `[macie] collect = findings | clean` the right name and place?
3. A tripped breaker in clean mode makes the run invalid: agreed?
