# Macie worklist

Ordered roughly by when we expect to do it. Blockers first; clean-ups
last. Add an item the moment something is deferred.

## Next

1. ~~**Transpiler: wrapper -> CVL.**~~ Done: `MacieConverter`. Pair 1 is
   reproduced exactly. Not in it yet: per-identifier detail caps from the
   rulesbase (`macie_cdi`'s optional 8th argument).
2. **Named-paths registration of `.macie.json`.** `add_named_paths_from_file`
   (the suffix filter in `paths_manager.py` and an `_is_odcs_path`-style
   check). Core change: agree the exact lines first. The full wrapper goes
   in the group's `_extra_data`.
3. **Pair 03_breaker.** A normative pair that trips the global breaker.

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

- **Header handling (#479).** The generated scan `$[1*]` assumes the
  header is line 0. Headerless files, leading blank lines, prolegomena
  lines and header-only files need a graceful answer. Related bug:
  `skip()` in the last expression skips the next line (#478).
- **Group C managed identifiers** (NAME, ADDRESS): unsupported. Report
  them as not translated rather than silently dropping them.
