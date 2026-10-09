# ODCS -> CsvPath normative pairs

Each subdirectory is one normative pair: an ODCS contract and the csvpath(s)
the converter must produce from it, plus data that proves the expected
csvpaths behave as intended. `tests/odcs/test_odcs_normative_pairs.py`
verifies the pairs themselves and requires the converter to reproduce them
exactly.

Layout of a pair:

    contract.yaml          ODCS input; must validate against the official
                           JSON Schema for its apiVersion
                           (csvpath/odcs/schemas/)
    expected/*.csvpath     converter output, one csvpath per schema object
    expected/report.yaml   (optional) what the converter must report as
                           skipped
    data/*.csv             sample data, conforming and non-conforming lines
    expected.yaml          per run: csvpath, data file, valid_lines, is_valid

Using the converter:

    from csvpath.odcs import OdcsContractLoader, OdcsConverter

    contract = OdcsContractLoader.from_path(path="orders.odcs.yaml")
    conversion = OdcsConverter(contract=contract).convert()
    conversion.csvpaths["orders"]    # csvpath text, one per schema object
    conversion.report.skipped        # what was not translated

## Conversion decisions (agreed with David, 2026-10-09)

Scope and shape

- ODCS -> CsvPath only, for now. CsvPath -> ODCS is later, if at all.
- Supported apiVersions: v3.0.x, v3.1.0, v3.2.0. Anything else, and any
  contract that is not valid against its official JSON Schema, raises
  `OdcsException`. So do a contract with no schema objects, a schema
  object with no properties, and duplicate schema object names.
- One schema object (one table) becomes one csvpath. Grouping csvpaths into
  named-paths groups is a later stage in the main codebase, not here.
- The generated csvpath has no filename in its root (`$[...]`), as for any
  csvpath loaded into a named-paths group.
- Metadata comment: `id` (the schema object name), `odcs-contract-id`,
  `odcs-contract-version`, `odcs-schema-object`, `validation-mode`.

Matching and validation semantics

- The csvpath matches valid (conforming) lines.
- Every generated csvpath carries
  `validation-mode: print, no-raise, no-fail, no-stop` in its metadata
  comment. Users edit that to change behavior.
- Properties map to `line()` wherever practical, trusting ODCS property
  order as column order. `line()` reads like SQL DDL, which keeps the
  cognitive load low for people new to CsvPath.
- `required` -> `.notnone`, `unique` -> `.distinct`. `primaryKey` alone
  implies neither, because a primary key may be composite.
- Checks that cannot go in the `line()` follow it. On an optional column
  they are wrapped as `or( empty(#c), <check> )`; on a required column
  they stand alone, since the `line()` already rejects empty values.

Header names

- The header is `physicalName` when present, else `name`.
- Names of letters, digits, `-`, `.`, `_` are written `#name`; names that
  also contain spaces are written `#"Order ID"`; anything else, and any
  all-digit name (which would read as a column index), is written by
  column index, e.g. `#4`.

Types

- `string` -> `string(#c, max, min)` from `maxLength`/`minLength`
  (`none()` for a missing max). `format` `email`/`uuid`/`uri` ->
  `email()`/`uuid()`/`url()`; these take no lengths, so lengths given with
  them are reported. Other formats are reported.
- `integer` -> `integer()`, `number` -> `decimal()`, with
  `maximum`/`minimum` as the max/min arguments. `exclusiveMinimum X` ->
  `gt(#c, X)`; `exclusiveMaximum X` -> `gt(X, #c)`.
- `boolean`, `date`, `timestamp`, `time`: see below and the framework
  workarounds.
- No `logicalType` -> `string`.
- `array`/`object`/`map`/`vector` -> `blank(#c)`, reported.
- Any `logicalTypeOptions` key not handled for the type (e.g.
  `multipleOf`) is reported.

File-level checks

- File-level rules (`rowCount`, and threshold counts) report through
  `fail()` and the csvpath's `is_valid`, not through matching.
- They need a `$[*]` scan, because with `$[1*]` a header-only file never
  reaches `last()`. Only csvpaths with file-level checks use this form;
  all others use the simpler `$[1*]`. Order inside the `$[*]` form:

      $[*][
          and.nocontrib( last(), lte( subtract(total_lines(), 1), 0 ) ) -> fail()
          first_line.nocontrib() -> @currency_invalid = 0
          first_line.nocontrib() -> skip()
          line( ... )
          ... per-line checks ...
          not.nocontrib( or( empty(#currency), in(#currency, "USD|EUR|GBP") ) ) -> counter.currency_invalid(1)
          and.nocontrib( last(), gte( @currency_invalid, 3 ) ) -> fail()
      ]

  `rowCount` checks come before the header skip, so a header-only file is
  checked too. Counters are initialized to 0 on the header line so the
  final check never compares against an unset variable. Threshold checks
  come last, after the last line has been counted; on a header-only file
  they do not run (there is nothing to count).

Quality rules with thresholds

- A zero threshold (`mustBe: 0`, `mustBeLessThan: 1`,
  `mustBeLessOrEqualTo: 0`) is a per-line constraint: offending lines do
  not match.
- A non-zero threshold (e.g. `mustBeLessThan: 5`) does both: offending
  lines do not match, AND a counted, file-level check is made at the last
  line with `fail()`. The run continues collecting matching lines; it does
  not stop.
- Threshold operators are emitted as a direct "fail when" condition, never
  wrapped in `not()`, and never using `lt()` (issue #301):

      mustBe X                  fail when neq(v, X)
      mustNotBe X               fail when eq(v, X)
      mustBeLessThan X          fail when gte(v, X)
      mustBeLessOrEqualTo X     fail when gt(v, X)
      mustBeGreaterThan X       fail when lte(v, X)
      mustBeGreaterOrEqualTo X  fail when gt(X, v)
      mustBeBetween [a, b]      fail when gt(a, v) or gt(v, b)
      mustNotBeBetween [a, b]   fail when gte(v, a) and gte(b, v)

- Percent thresholds (`unit: percent`) are not yet supported; reported.

Library metrics

- `rowCount` (schema level): checked on `subtract(total_lines(), 1)`.
- `invalidValues` (property): `arguments.validValues` -> `in()`,
  `arguments.pattern` -> `regex()`, both -> `and()`. The counter counts
  non-empty values that break the rule; empty values are
  `nullValues`/`missingValues`, not `invalidValues`.
- `nullValues` (property): any threshold makes the column `.notnone`, so
  lines with a null do not match; a non-zero threshold also counts
  `empty.nocontrib(#c)`.
- `duplicateValues` (property): zero threshold -> `.distinct`. Non-zero
  thresholds, and schema-level (multi-column) `duplicateValues`, are not
  yet supported; reported.
- `missingValues` is not yet supported; reported.
- v3.0's deprecated `rule` key is read the same as `metric`.

Allowed values

- Both forms are supported: the v3.2.0 property `enum` (EnumValue objects,
  `- value: open`, or plain values), and the v3.0/v3.1 property quality
  rule `metric: invalidValues` with `arguments.validValues`.
- Values become `in()`'s pipe-delimited string. A value containing `|` or
  `"` cannot be expressed; the whole value list is reported.

Dates, timestamps, and times (pair 03)

- `date` -> `date()`, `timestamp` -> `datetime()`, `time` -> `datetime()`
  with a time-only format.
- `format` is a JDK DateTimeFormatter pattern, translated to strftime.
  Quoted literals (`'T'`) are honored. Unquoted letters with no JDK
  meaning, such as the `T` in the ODCS docs' own `yyyy-MM-ddTHH:mm:ssZ`,
  are treated as literals. `Z`/`X` offsets become `%z`. `SSS` becomes
  `%f`, which is lenient (1-6 digits). JDK fields with no strftime
  equivalent (e.g. era, quarter, week) are reported and the values are
  parsed leniently instead.
- No `format`: `date` -> ISO `%Y-%m-%d`; `time` -> `%H:%M:%S`;
  `timestamp` -> parsed leniently (no format argument).
- `minimum`/`maximum`/`exclusiveMinimum`/`exclusiveMaximum` become
  `gte()`/`lte()`/`gt()` comparisons of `date()`/`datetime()` values
  outside the `line()`. ODCS does not say what format bounds are written
  in, so a bound is parsed with the property's format first, then ISO, and
  emitted with whichever format parsed it. A bound neither parses is
  reported.
- `timezone`/`defaultTimezone` are accepted without a separate check; an
  offset in the format (`Z`/`X`) is what enforces a timezone.

Unsupported features and the conversion report (pair 04)

- Validation-relevant features the converter cannot translate are skipped
  and listed in the report: `object`, `location` (path within the schema
  object, `properties.<name>` selecting by name), `feature`, `reason`.
- Report order: per schema object, schema-level quality, then properties
  in order, then schema-level relationships.
- A skipped property still appears in the `line()` (as `blank()` for
  untyped values), so the header order is still checked.
- Non-validation sections (team, servers, SLA, support, price, roles,
  tags, authoritative definitions, custom properties, descriptions) are
  ignored silently and not reported.

Known framework issues and workarounds

- `date()`/`datetime()` inside `line()` reject empty values even without
  `notnone` (issue #300). Until fixed, optional dates are emitted as
  `blank(#d)` in the `line()` plus `or( empty(#d), date(#d, "<fmt>") )`.
  Required dates use `date.notnone(#d, "<fmt>")` in the `line()` directly.
  `unique` on an optional date cannot be checked; it is reported.
- `boolean()` has the same empty-value behavior inside `line()` (noted on
  #300). In addition, nested in `or()`/`not()`, `boolean()` treats invalid
  values such as `perhaps` as matches (issue #302). So optional booleans
  are emitted as `blank(#b)` in the `line()` plus
  `or( empty(#b), in( lower( strip(#b) ), "true|false|1|0" ) )`, which
  accepts exactly what `boolean()` accepts. Required booleans use
  `boolean.notnone(#b)` in the `line()` directly.
- `lt()`/`below()`/`before()` behave as `lte()` (a missing `return` in
  `csvpath/matching/functions/math/above.py`, issue #301). The converter
  never emits them; `gt()`, `gte()`, and `lte()` are correct.
- `print()` appears to drop messages containing `(` or `@`. The converter
  does not emit `print()` for now.

Regular expressions

- ODCS patterns (ECMA-262) become CsvPath `/.../` regex literals, run by
  Python `re`. Unescaped `/` in a pattern is escaped. A pattern Python
  `re` cannot compile (e.g. an ECMA named group `(?<n>...)`) is reported.
- The regex goes in the first argument of `regex()`, so a data value that
  begins with `/` cannot be mistaken for the regex.
- `regex()` strips every leading and trailing `/` from the literal, so a
  pattern that begins or ends with an escaped slash would lose it. The
  converter wraps such a pattern in a non-capturing group: `(?:abc\/)`.
