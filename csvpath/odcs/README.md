# ODCS to CsvPath

Converts [Open Data Contract Standard](https://bitol-io.github.io/open-data-contract-standard/)
(ODCS) data contracts into CsvPath Validation Language. Each table in a
contract becomes one csvpath that validates a delimited file against that
table's schema and quality rules.

**Status:** working, tested, and not yet wired into the rest of the
Framework. Nothing outside this package uses it yet. Loading ODCS contracts
directly into named-paths groups is planned.

## Quick start

```python
from csvpath.odcs import OdcsContractLoader, OdcsConverter

contract = OdcsContractLoader.from_path(path="orders.odcs.yaml")
conversion = OdcsConverter(contract=contract).convert()

conversion.csvpaths            # {"orders": "<csvpath text>", ...} one per table
conversion.report.skipped      # what could not be translated, and why
```

The generated csvpaths have no filename in their root (`$[...]`), so they
load like any named-paths group:

```python
from csvpath import CsvPaths

paths = CsvPaths()
paths.file_manager.add_named_file(name="orders", path="orders.csv")
paths.paths_manager.add_named_paths(
    name="orders", paths=[conversion.csvpaths["orders"]]
)
paths.collect_paths(pathsname="orders", filename="orders")
for result in paths.results_manager.get_named_results("orders"):
    print(result.is_valid, result.lines.to_list())
```

`OdcsContractLoader` also has `from_string(text=...)` for YAML or JSON
text, and `validate(contract=...)` for an already-parsed dict.

## An example

This ODCS table:

```yaml
schema:
  - name: orders
    properties:
      - name: order_id
        logicalType: string
        required: true
        unique: true
        logicalTypeOptions: { pattern: "^ORD-[0-9]{6}$" }
      - name: customer_email
        logicalType: string
        logicalTypeOptions: { format: email }
      - name: quantity
        logicalType: integer
        required: true
        logicalTypeOptions: { minimum: 1, maximum: 999 }
      - name: status
        logicalType: string
        enum: [ { value: open }, { value: shipped }, { value: cancelled } ]
      - name: order_date
        logicalType: date
        required: true
        logicalTypeOptions: { format: yyyy-MM-dd }
    quality:
      - metric: rowCount
        mustBeGreaterThan: 0
```

becomes:

```
~
  id: orders
  odcs-contract-id: orders-contract
  odcs-contract-version: 1.0.0
  odcs-schema-object: orders
  validation-mode: print, no-raise, no-fail, no-stop
~
$[*][
    and.nocontrib( eq( count_lines(), total_lines() ), lte( subtract(total_lines(), 1), 0 ) ) -> fail()
    first_line.nocontrib() -> skip()
    line(
        string.notnone.distinct(#order_id),
        email(#customer_email),
        integer.notnone(#quantity, 999, 1),
        string(#status),
        date.notnone(#order_date, "%Y-%m-%d")
    )
    regex(/^ORD-[0-9]{6}$/, #order_id)
    or( empty(#status), in(#status, "open|shipped|cancelled") )
]
```

## What to expect from a generated csvpath

- **It matches the valid lines.** A line that breaks any translated rule
  does not match. Collect the matches to get the conforming data.
- **File-level rules set `is_valid`.** `rowCount` and quality thresholds
  (e.g. "fewer than 3 invalid currencies") call `fail()`, so check
  `is_valid` after the run. The run does not stop on a failure; it keeps
  collecting valid lines.
- **`validation-mode: print, no-raise, no-fail, no-stop`** is set in every
  csvpath's metadata. Edit it to change how validation errors are handled.
- **Columns are checked in ODCS property order**, with `line()`. The header
  is `physicalName` if given, else `name`.
- **Empty values are never duplicates**, as in SQL: an optional `unique`
  column may have any number of empty values.
- **Trailing blank lines are harmless.** They are not counted as rows and
  do not hide file-level checks.

## What is translated

| ODCS | CsvPath |
|---|---|
| `logicalType` string, integer, number, boolean, date, timestamp, time | `string()`, `integer()`, `decimal()`, `boolean()`, `date()`, `datetime()` |
| `required`, `unique` | `.notnone`, `.distinct` (or a `has_dups()` check on optional columns) |
| `minLength`/`maxLength`, `minimum`/`maximum` | type function arguments |
| `exclusiveMinimum`/`exclusiveMaximum` | `gt()` checks |
| `pattern` | `regex()` |
| `format` email, uuid, uri | `email()`, `uuid()`, `url()` |
| date/time `format` (JDK patterns) | strftime formats |
| date bounds | `gte()`/`gt()`/`lte()` on `date()` values |
| `enum` (v3.2), `invalidValues` + `validValues` (v3.0/3.1) | `in()` |
| integer `multipleOf` | `mod()` |
| quality `rowCount` | row count check, sets `is_valid` |
| quality `nullValues`, `missingValues`, `invalidValues`, `duplicateValues` (one column or several) | per-line checks, plus counted thresholds in rows or percent |
| contract id and version, table name | csvpath metadata |

Supported ODCS versions: v3.0.x, v3.1.0, v3.2.0. A contract is validated
against the official ODCS JSON Schema for its version before conversion.

## What is not translated

These are skipped and listed in `conversion.report.skipped`, each with the
table, the location in the contract, a feature label, and a reason:

- relationships (foreign keys between tables)
- `array`, `object`, `map`, and `vector` properties (the column is still
  checked for presence)
- string formats with no CsvPath function, e.g. `ipv4`, `hostname`
- patterns Python's `re` cannot compile, e.g. ECMA named groups
- quality rules of type `sql`, `custom`, and `text`
- non-integer `multipleOf` and percent `rowCount`
- a table with no properties (e.g. a schema held in a schema registry)

Sections that do not describe data (team, servers, SLAs, pricing, roles,
support, tags) are ignored and not reported.

`OdcsException` is raised only for input that cannot be converted at all:
an unparseable or schema-invalid contract, an unsupported version, no table
with properties, or duplicate table names.

## More detail

- `tests/odcs/test_resources/normative/README.md` records every conversion
  rule and why it is the way it is, with five worked contract/csvpath
  pairs beside it.
- The converter works around a few CsvPath function issues: #300, #301,
  #302, #305, #306, and #308.
