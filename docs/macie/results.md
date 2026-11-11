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

## When setup fails

If a Macie function cannot be set up (a bad allow list, a missing catalog
snapshot), the run is marked invalid, stops, and says so on the `macie`
stream:

```
macie: cannot run: <the reason>
```

It never runs as if the failing piece were absent.
