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

## Validating reference-v3 against the corpus

`test_normative_examples.py` runs real reference-v3 expressions (the
`FilesReferenceFinder3`/`ResultsReferenceFinder3`/`CsvpathsReferenceFinder3`
classes under `csvpath/references/`) against the committed corpus and
asserts on ground-truth results, catching the same way as any other pytest
module:

```
poetry run pytest tests/corpus/test_normative_examples.py -v
```

This is a different layer than `tests/references/`'s own unit tests, which
exercise the finders against hand-built, synthetic manifest fixtures — a
pass here proves the finder's expectations about manifest/directory shape
match what production registration/run code actually writes. It's a
representative first pass (one or two cases per major construct family from
`specs/references_v3/spec/normative_reference_examples.txt`), not a
line-by-line transcription of the whole spec — extend it as the corpus
grows. Three known gaps found by this validation pass are recorded as
`xfail(strict=True)` tests in `TestKnownGaps` rather than fixed (core-code
changes are out of this repo's current tests-only scope) — see that class's
own docstrings/reasons for the specifics.

## Testing subagent interpretation of the corpus

`scenarios.yaml` is a bank of natural-language questions about the corpus's
state, each with a crisp, checkable ground-truth answer — for testing
whether an agent can correctly explore and interpret the corpus and
communicate an accurate answer back, as opposed to whether reference-v3
itself resolves correctly (that's what `test_normative_examples.py` is for).

To run a scenario against an agent:

1. Give the agent the scenario's `question` text, plus access to this
   repository (at minimum `tests/corpus/data/`, `tests/corpus/assets.yaml`,
   and this README for background). Don't give it `scenarios.yaml` itself —
   that hands over the answer.
2. Capture its final answer as plain text.
3. Grade it:
   ```
   poetry run python tests/corpus/grade_scenario.py <scenario_id> "<answer text>"
   ```
   Exit code 0 means PASS, 1 means FAIL. `grade_scenario.py --all answers.json`
   grades a batch at once (a JSON object mapping scenario id to answer text).

There's no API wired up to spawn an agent directly from the grading script —
Claude Code's own Agent tool is only callable from inside a Claude Code
session. The intended flow is for a human or an orchestrating session to
hand off the question, capture the answer, and grade it.

## Design notes / known limitations (v1)

- **Content-fingerprint dedup**: CsvPath Framework dedupes identical content
  silently. Named-paths groups now accumulate for real across repeat
  versions — each one after the first is a genuine
  `PathsManager.add_named_paths(paths=[...], append=True)` call that adds
  one more trivial statement onto whatever content the group already had,
  rather than mutating the pristine original independently each time.
  Named-files groups have no equivalent append mode, so repeat CSV versions
  are still independent mutations of the pristine original (duplicating the
  source's own last row `count - 1` times, so each version is still
  genuinely distinct from every other).
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
