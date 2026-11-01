# Macie worklist

Ordered roughly by when we expect to do it. Blockers first; clean-ups
last. Add an item the moment something is deferred.

## Next

1. ~~**Transpiler: wrapper -> CVL.**~~ Done: `MacieConverter`. Pair 1 is
   reproduced exactly. Not in it yet: per-identifier detail caps from the
   rulesbase (`macie_cdi`'s optional 8th argument).
2. ~~**Named-paths registration of `.macie.json`.**~~ Done:
   `add_named_paths_from_file` and `add_named_paths_from_dir` load
   wrappers like ODCS contracts. The wrapper is copied into the group home
   with `<file>.report.json` beside it. A Macie csvpath's id must be
   unique in its group (David, 2026-10-31).
3. **Pair 03_breaker.** A normative pair that trips the global breaker.

## Design questions to revisit

- **Should findings ever make a run invalid?** A Macie csvpath stays
  `is_valid` even with HIGH findings, so a group can look valid while it
  holds sensitive data.
- **A csvpath after a Macie csvpath with `source-mode: preceding`** gets
  only the lines with findings. That could be a feature (e.g. redaction)
  or a surprise.
- **Limits are fixed at registration**: changing `[macie]` in config.ini
  takes effect when the group is reloaded. David is not worried about this
  for now (2026-10-31).

## After that

4. **Managed identifiers, group A** (format plus checksum, e.g. credit
   cards with Luhn): `macie_mdi`, with pair 02_credit_card.
5. **Text allow lists**: `macie_allow_words` via `load_list()` (#470).
   #470 is a general function: message the refs-v3 session (csvpath-35)
   before starting it.
6. **Managed identifiers, group B** (format plus keyword).
7. **boto3 download** into a wrapper. Needs an AWS account, region and
   permissions agreed with David first.
8. **One-time fidelity scan against real Macie** (billed; ask first) to
   confirm the three interpretations in transpile-design.md.

## Clean-ups (not blockers)

- **Stale source copies in group homes (Macie and ODCS).** Reloading a
  group without append rewrites `group.csvpaths` but leaves the wrapper and
  contract copies, and their `.report.json` files, from earlier loads. The
  group home can then describe rules it no longer runs. Cleanup should be
  automatic (David, 2026-10-31).
- **Directory loads under a name** refuse Macie wrappers, as they refuse
  ODCS contracts. Appending with `add_named_paths_from_file(append=True)`
  works for both.

- **Header handling (#479).** The generated scan `$[1*]` assumes the
  header is line 0. Headerless files, leading blank lines, prolegomena
  lines and header-only files need a graceful answer. Related bug:
  `skip()` in the last expression skips the next line (#478).
- **Group C managed identifiers** (NAME, ADDRESS): unsupported. Report
  them as not translated rather than silently dropping them.
