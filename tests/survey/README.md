# Validation output survey (#779)

Tools that inventory quirks in validation output: error messages, printed errors, collected errors and raise behavior. They are not collected by pytest; run them on demand from the repo root, with cloud providers off.

1. `message_sites.py` lists every line that can produce a message (handle_error, raise, re-raise). It is the denominator for coverage.
2. `harness.py` runs bad inputs through every function, seeded from the alias smoke test's CALLS. It varies the bad values, argument shapes, placements and error policies, and writes JSON lines, one run per line.
3. `detectors.py` flags quirks in the runs and groups them by message template into a report.
4. `site_coverage.py` takes a coverage run of the harness and reports the share of message sites reached.

Heavy runs (the harness, and especially the harness under coverage) use 2 workers by default. On the shared VM, run them one at a time under the agreed lock (see the CVL hardening notes).

```
python tests/survey/message_sites.py --out sites.json
python tests/survey/harness.py --out runs.jsonl --jobs 2
python tests/survey/detectors.py runs.jsonl --report report.md --json groups.json
coverage run --rcfile=<rc with parallel, concurrency=multiprocessing> tests/survey/harness.py --out runs.jsonl
coverage combine --rcfile=<rc>
python tests/survey/site_coverage.py --data <.coverage>
```
