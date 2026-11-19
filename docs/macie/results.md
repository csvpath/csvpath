# Results and findings

A Macie csvpath produces four outputs. Each has one job:

| Output | Where | What |
|---|---|---|
| Matched lines | the run's `data.csv` | the lines with at least one finding |
| Detail | the `macie` print stream (`macie.txt`) | one line per detailed occurrence, and a summary per identifier |
| Errors | the run's `errors.json` | the same detail lines, one error per detailed occurrence |
| Findings | the `macie_findings` variable (`vars.json`) | all findings, in Macie's own shape |

**No output contains the sensitive value.** Every output gives an
occurrence's location (line, row, column, column name), as Macie's own
findings do.

## The `macie` print stream

```
macie EmployeeId: occurrence 1, line 1 (row 2), column 3 employee_id
macie EmployeeId: occurrence 2, line 5 (row 6), column 4 manager_note
macie EmployeeId: 5 occurrences, severity MEDIUM, detail shown for first 2
macie BadgeId: 1 occurrence, severity MEDIUM, detail shown for all 1
```

- A detail line names the identifier, its running occurrence number, the
  CsvPath line, the Macie row, and the column number and name.
- A summary line gives each identifier's exact count, its severity for
  the file, and how much detail was shown.
- An identifier below its lowest severity threshold has no finding, as in
  Macie: `severity none (below 3)`.

### Row and column numbers

Findings use Macie's numbering, so they can be compared cell by cell with
real Macie findings: `row` is 1-based with the header as row 1, and
`column` is 1-based. CsvPath line `n` is Macie row `n + 1`. Detail lines
give both.

### When the first line is not a header

The first line is read as the header. Its names are each cell's
`columnName`, and a keyword in it covers its column. If the first line
holds a value one of the csvpath's identifiers finds (a file with no
header, whose first line is data), it is read as data instead, as Macie
reads it: cells have no `columnName` (null), detail lines give the
column number only, no header keyword applies, and the run says so,
once, on the `macie` stream and in its errors:

```
macie: the first line holds a value an identifier finds, so it is read as data, not a header: column names and header keywords are not used, and the first line is not scanned
```

The first line is not scanned, so a value on it is not reported. Give
such files a header line.

## The findings document

`macie_findings` follows Macie's sensitive data findings: custom
identifiers under `customDataIdentifiers`, managed identifiers under
`sensitiveData` by category.

```json
{
  "customDataIdentifiers": {
    "detections": [
      {
        "arn": "arn:aws:macie2:us-east-1:123456789012:custom-data-identifier/2a1b7e4c-...",
        "name": "EmployeeId",
        "count": 5,
        "severity": "MEDIUM",
        "occurrences": {
          "cells": [
            { "cellReference": null, "column": 3, "columnName": "employee_id", "row": 2 }
          ]
        }
      }
    ],
    "totalCount": 5
  },
  "sensitiveData": [
    {
      "category": "PERSONAL_INFORMATION",
      "detections": [
        {
          "type": "HTTP_COOKIE",
          "count": 4,
          "severity": "MEDIUM",
          "occurrences": {
            "cells": [
              { "cellReference": null, "column": 3, "columnName": "notes", "row": 4 }
            ]
          }
        }
      ],
      "totalCount": 6
    }
  ],
  "csvpath": {
    "source_arn": "arn:aws:macie2:us-east-1:123456789012:classification-job/6a7b8c9d...",
    "stopped": false,
    "stopped_at_line": null,
    "max_findings": 10000,
    "max_detail": 15
  }
}
```

- `count` is exact, one per occurrence; `cells` holds up to 15 locations,
  the cap Macie uses, each cell once however many occurrences it holds.
- `csvpath` is ours: the Macie job or template the rules came from, and
  whether the run stopped early (below).

## Limits

Reporting each occurrence costs more than counting it, so there are two
limits, set in `config.ini` `[macie]` and written into the csvpath when
the group is loaded:

- **`max_detail`** (default 15): after this many occurrences of one
  identifier, no more detail lines or errors for it. Counting goes on,
  so counts and severities stay exact; the summary says "detail shown for
  first N".
- **`max_findings`** (default 10000): when occurrences across all
  identifiers reach this, the file stops. The results are partial and say
  so:

  ```
  macie: stopped at line 18450 after 10000 occurrences (max 10000); results are partial and severities are at least as shown
  ```

  and the findings document has `"stopped": true` and the line.

## Clean lines

A Macie csvpath collects the lines with findings. With
`[macie] collect = clean` it collects the clean lines instead, those
with no findings, so a csvpath after it in the group with
`source-mode: preceding` reads only those. One use is passing on what is
safe to a less trusted stage, with the findings as the record of what
was held back. The findings, errors and printouts are the same in both
modes.

The setting is read when the group is loaded, like the limits. The
loaded csvpath has `return-mode: no-matches` and `macie-collect: clean`
in its metadata.

**Clean means clean of the identifiers translated.** `NAME` and
`ADDRESS` are not checked line by line, even when Jev checks them: Jev
judges whole columns after the last line. The run says which are not
checked:

```
macie: clean lines are checked for 7 identifiers; not checked: NAME
```

**A tripped breaker fails the run.** The lines after the stop are never
scanned, so they are not among the clean lines, and a csvpath reading
them would get a short file. In clean mode the run is invalid, and
the run says so:

```
macie: breaker tripped at line 4; lines after it were not scanned and are not among the clean lines
```

The Macie csvpath also calls `stop_all()`. A breadth-first run (the
`_by_line` methods) then stops its other csvpaths at that line, and a
serial run (`collect_paths()`, `fast_forward_paths()`, `next_paths()`)
does not run the csvpaths after it. In findings mode a tripped breaker
leaves the run valid, as before.

## The Jev review

With `[macie] review` on, each reviewed detection gains a `review` list and
the `csvpath` section a `review` summary. Nothing else in the document
changes. See [reviewing findings with Jev](review.md).

## NAME and ADDRESS

With `NAME` or `ADDRESS` in `[macie] review`, the document gains a `jev`
section: Jev's check of the file's columns, kept apart from the
Macie-shaped `sensitiveData` because it is a model's judgment, not
Macie's rules. See [NAME and ADDRESS](review.md#name-and-address).

## When setup fails

If a Macie function cannot be set up (a bad allow list, a missing catalog
snapshot), the run is marked invalid, stops, and says so on the `macie`
stream:

```
macie: cannot run: <the reason>
```

It never runs as if the failing piece were absent.
