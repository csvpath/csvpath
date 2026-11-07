# Quickstart

This walks one Macie classification job from its wrapper file to its
findings. It uses the example wrapper and data in the repository, under
`tests/macie/test_resources/normative/09_text_allow_list/`: a job with one
custom data identifier (employee ids, `EMP-` and 6 digits) and one text
allow list of contractor ids that are not to be reported.

The same steps are a runnable test you can step through:
`poetry run pytest -s tests/csvpaths/test_csvpaths_macie_walkthrough.py`.

## 1. A wrapper

A `.macie.json` wrapper holds one Macie job's whole setup. The Framework
will download it from your AWS account (planned; see
[limitations](limitations.md)); today you start from a wrapper file. Its
format is in `specs/macie/wrapper-format.md`.

## 2. Load it into a named-paths group

```python
from csvpath import CsvPaths

paths = CsvPaths()
paths.paths_manager.add_named_paths_from_file(
    name="hr_ids",
    file_path="hr-contractor-allow.macie.json",
)
```

The file suffix `.macie.json` is what marks a Macie wrapper. Loading:

- converts the wrapper to one csvpath, named for the Macie job;
- stores the text allow list in the group's assets;
- stores the managed identifier catalog the conversion used, as
  `assets/macie_catalog.json`;
- copies the wrapper, byte for byte, into the group home, with its
  conversion report beside it.

```
named_paths/hr_ids/
  group.csvpaths                                the generated csvpath
  hr-contractor-allow.macie.json                the wrapper, as loaded
  hr-contractor-allow.macie.json.report.json    what was and was not translated
  assets/
    c0n7r4a1c7o9r5s3a6l0lw.txt                  the text allow list, by its Macie id
    macie_catalog.json                          the catalog snapshot
  manifest.json, definition.json, README.md     as for every group
```

The generated csvpath starts with metadata recording where the rules came
from and the limits used. (This example sets `[macie] max_detail = 3` in
`config.ini`, so only the first 3 occurrences are detailed; the default is
15.)

```
~
  id: hr-contractor-allow
  macie-origin: job
  macie-job-id: 6e1d5b2f9c8a7f6e5d4c3b2a1f0e9d8c
  macie-account: 123456789012
  macie-region: us-east-1
  macie-source-arn: arn|aws|macie2|us-east-1|123456789012|classification-job/6e1d5b2f9c8a7f6e5d4c3b2a1f0e9d8c
  macie-downloaded-at: 20261029T174000Z
  macie-max-findings: 10000
  macie-max-detail: 3
  logic-mode: OR
  print-mode: separate
  ...
~
```

(The ARN is written with `|` for `:`, since `:` separates metadata keys.)

A directory of wrappers loads with `add_named_paths_from_dir()`, one group
per wrapper, each named for its file without `.macie.json`.

## 3. Register the data

```python
paths.file_manager.add_named_file(name="employees", path="employees.csv")
```

## 4. Run the group

```python
paths.collect_paths(filename="employees", pathsname="hr_ids")
result = paths.results_manager.get_named_results("hr_ids")[0]
```

`collect_paths()` collects the lines that have at least one finding.
Lines with no finding are not matched.

## 5. Read the results

The summary and each detailed occurrence are on the `macie` print stream:

```python
for line in result.get_printouts("macie"):
    print(line)
```

```
macie EmployeeId: occurrence 1, line 1 (row 2), column 3 employee_id
macie EmployeeId: occurrence 2, line 5 (row 6), column 4 manager_note
macie EmployeeId: occurrence 3, line 7 (row 8), column 4 manager_note
macie EmployeeId: 5 occurrences, severity MEDIUM, detail shown for first 3
```

The findings, in Macie's own shape, are in the `macie_findings` variable
(and so in the run's `vars.json`):

```python
findings = result.csvpath.variables["macie_findings"]
findings["customDataIdentifiers"]["detections"][0]["count"]    # 5
findings["customDataIdentifiers"]["detections"][0]["severity"] # "MEDIUM"
```

Printouts and findings give each occurrence's location, never the
sensitive value itself. See [results](results.md).

## 6. What the run kept

Every group run copies its Macie inputs into its run directory, with their
sha256 hashes, so it can be replicated with exactly the rules it used:

```
archive/hr_ids/2026-11-07_22-25-11/
  _extra_data/macie/
    hr-contractor-allow.macie.json
    hr-contractor-allow.macie.json.report.json
    macie_catalog.json
    lists/c0n7r4a1c7o9r5s3a6l0lw.txt
    inputs.json
  hr-contractor-allow/
    data.csv  errors.json  macie.txt  vars.json  manifest.json  meta.json
```

See [reproducibility](reproducibility.md).

## Settings

In `config.ini`:

```ini
[macie]
# stop the file after this many occurrences across all identifiers
max_findings = 10000
# print and record detail for this many occurrences per identifier
max_detail = 15
# the project rulesbase for customizing the stand-ins
rulesbase = rulesbase
```

All three are optional; the values shown are the defaults. The limits
are read when a wrapper is loaded and written into the csvpath's
metadata, so a loaded group keeps them.
