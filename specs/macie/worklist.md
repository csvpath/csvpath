# Macie worklist

Ordered roughly by when we expect to do it. Blockers first; clean-ups
last. Add an item the moment something is deferred.

## Next

1. ~~**Transpiler: wrapper -> CVL.**~~ Done: `MacieConverter`. Pair 1 is
   reproduced exactly. Not in it yet: per-identifier detail caps from the
   rulesbase (`macie_cdi`'s optional 8th argument).
2. ~~**Loading `.macie.json` into named-paths groups.**~~ Done:
   `add_named_paths_from_file` and `add_named_paths_from_dir` load
   wrappers like ODCS contracts. The wrapper is copied into the group home
   with `<file>.report.json` beside it. A Macie csvpath's id must be
   unique in its group (David, 2026-10-31).
3. ~~**Pair 03_breaker.**~~ Done. It needed the `stop()` fix (#483, PR
   #484) so the line that trips the breaker is matched.

## Design questions to revisit

- **Should findings ever make a run invalid?** A Macie csvpath stays
  `is_valid` even with HIGH findings, so a group can look valid while it
  holds sensitive data.
- **A csvpath after a Macie csvpath with `source-mode: preceding`** gets
  only the lines with findings. That could be a feature (e.g. redaction)
  or a surprise.
- **Limits are fixed when the group is loaded**: changing `[macie]` in config.ini
  takes effect when the group is reloaded. David is not worried about this
  for now (2026-10-31).

## After that

4. ~~**Managed identifiers, group A, first batch: credit cards.**~~ Done:
   `macie_mdi`, the packaged catalog, `CreditCardDetector`, Luhn, and pair
   02_credit_card. More group A identifiers next (SSN, IBAN mod-97, NPI,
   ...), each a catalog entry plus a detector.
4a. **Project rulesbase for the stand-ins.** Copy the packaged catalog into
   the project on load, never overwrite it, resolve a hierarchy (project,
   then Framework, then a `common.json` shared with other rule systems).
   From David's notes; deferred until there is more than one identifier
   to customize (David, 2026-11-01).
5. **Text allow lists**: `macie_allow_words` via `load_list()` (#470).
   #470 is a general function: message the refs-v3 session (csvpath-35)
   before starting it.
6. **Managed identifiers, group B** (format plus keyword).
7. **boto3 download** into a wrapper. Needs an AWS account, region and
   permissions agreed with David first.
8. **One-time fidelity scan against real Macie** (billed; ask first) to
   confirm the interpretations in transpile-design.md: three for custom
   identifiers, four for managed ones.

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
