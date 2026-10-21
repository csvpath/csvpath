# Reference-v3 test corpus

A small, deterministic set of CsvPath Framework-managed named-files,
named-paths, and run archives under `tests/corpus/data/`, spread across a
simulated ~90-day history. It exists so that reference-v3 expressions
(`:groups()`, `:from()`/`:to()`, `:status()`, date-mode selectors, etc.) have
real, representative data to test and explore against instead of relying on
David manually re-testing the spec by hand on every release.

## What's here

- `assets.yaml` — the source-of-truth asset list. Edit this to grow the
  corpus (add a group, add a version, add a run).
- `generate.py` — regenerates `data/` from `assets.yaml` by driving the real
  CsvPath Framework registration/run code (`FileManager.add_named_file`,
  `PathsManager.add_named_paths`, `CsvPaths.fast_forward_paths`), not by
  hand-authoring manifests. Historical spread comes from
  `csvpath.util.date_util.DateUtility`'s `OFFSET_DAYS`, so every directory
  name and manifest timestamp is exactly what production code would have
  written at that point in simulated history.
- `config/config.ini` — a dedicated config pointing all inputs/results/cache
  at `tests/corpus/data/`, isolated from both the dev config and any other
  test config.
- `assets/` — small hand-written fixtures used by the generator itself
  (`generic_scan.csvpath`, a header-agnostic baseline statement usable
  against any CSV).
- `data/` — the generated output. Committed to git so the corpus is
  immediately usable without regenerating; also fully reproducible by
  running the generator.

## Regenerating

```
poetry run python tests/corpus/generate.py
```

Safe to re-run any time — it wipes and rebuilds `tests/corpus/data/` from
scratch. Only `assets.yaml` (and any new fixture it references under
`assets/`) needs editing to grow the corpus; `data/` is always a derived
artifact.

## Design notes / known limitations (v1)

- **Content-fingerprint dedup**: CsvPath Framework dedupes identical content
  silently, so each repeat "version" of the same source file is generated
  from a mutated scratch copy (CSVs: duplicate the last row; `.csvpath`/
  `.csvpaths`: append one more trivial, always-valid statement) to force a
  genuinely distinct fingerprint. These mutations currently do NOT
  accumulate — each version is mutated independently from the pristine
  original, so a later version's one added line/statement replaces rather
  than adds to an earlier version's. Good enough for exercising
  version-selection reference expressions; not yet a fully realistic
  "statements accumulate over time" simulation.
- **Template date tokens are unaffected by `DateUtility`**: `:year`,
  `:month_name`, `:day`, etc. in `TemplateUtility.transform_template` read
  real wall-clock time directly, not `DateUtility`. Only positional tokens
  (`:0`, `:1`, ...) and literal path segments are safe to use in a template
  here.
- **Failed registration trigger**: a deliberately-seeded "Registration
  failed" ledger entry (for `:status()` testing) requires an empty-string
  `path` to `add_named_file()` — a merely nonexistent-but-plausible path
  does NOT trigger it, since `FileManager.can_load()` is a load-policy check
  (HTTP/local-file permission flags), not a file-existence check. The empty
  path raises `ValueError`, which `generate.py` catches so the generator
  itself doesn't crash.
- **Deliberate edge cases currently seeded**: the failed registration above,
  and uneven template depth for `:groups()` (`orders` uses a 1-level
  template, `acme_invoices`/`zipcodes` use none).
