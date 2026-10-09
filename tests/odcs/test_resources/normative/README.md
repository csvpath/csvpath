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
  `OdcsException`. So do a contract with no schema objects, a contract
  where no schema object has properties, and duplicate schema object
  names.
- A schema object with no properties (ODCS allows the schema to live
  elsewhere, e.g. a Kafka schema registry) is reported and skipped; the
  other schema objects still convert.
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
- `required` -> `.notnone`. `primaryKey` alone implies neither required
  nor unique, because a primary key may be composite.
- `unique`: empty values are never duplicates (SQL semantics, agreed with
  David 2026-10-09). `.distinct` treats two empty values as duplicates, so
  it is only used on required columns, which reject empties anyway:
  `string.notnone.distinct(#c)`. An optional unique column, of any type,
  gets `or( empty(#c), not( has_dups(#c) ) )` after the `line()`.
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
- `multipleOf X` with an integer X -> `eq( mod(#c, X), 0 )`. A non-integer
  X is reported: `mod()` rounds to 2 places, so a float remainder near the
  divisor (`114.99999 % 5`) reads as `5.0`, not `0`.
- `boolean`, `date`, `timestamp`, `time`: see below and the framework
  workarounds.
- No `logicalType` -> `string`.
- `array`/`object`/`map`/`vector` -> `blank(#c)`, reported.
- Any `logicalTypeOptions` key not handled for the type (e.g.
  `multipleOf`) is reported.

File-level checks

- File-level rules (`rowCount`, and threshold counts) report through
  `fail()` and the csvpath's `is_valid`, not through matching.
- They run on the last line with data, identified by
  `eq( count_lines(), total_lines() )`: `count_lines()` counts non-blank
  lines seen so far and `total_lines()` counts non-blank lines in the
  file, the header included in both. `last()` is not used: a blank last
  line is processed frozen, and `last()` composed in `and()` does not run
  on a frozen line, so a file ending in a blank line would silently skip
  every file-level check. Blank lines are not data rows either:
  `subtract(total_lines(), 1)` counts only non-blank data lines.
- `rowCount` must also fail a header-only file, and with `$[1*]` a
  header-only file has no scanned line at all (issue #306). So a csvpath
  with a `rowCount` check uses the `$[*]` form, with the check before an
  explicit skip of the header line:

      $[*][
          and.nocontrib( eq( count_lines(), total_lines() ), lte( subtract(total_lines(), 1), 0 ) ) -> fail()
          first_line.nocontrib() -> skip()
          line( ... )
          ... per-line checks ...
      ]

- Threshold counts work in either form, so they do not force `$[*]`.
  Counters come after the per-line checks, then the checks on the last
  line with data:

      not.nocontrib( or( empty(#currency), in(#currency, "USD|EUR|GBP") ) ) -> counter.currency_invalid(1)
      and.nocontrib( eq( count_lines(), total_lines() ), gte( @currency_invalid, 3 ) ) -> fail()

  `counter()` creates its variable at 0 on first evaluation, so counters
  need no initialization and a check never sees an unset variable. On a
  header-only file there is nothing to count and the check does not run.
- Everything else uses the simpler `$[1*]`.
- Each pair with file-level checks has a data file ending in blank lines
  to keep this covered.

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

- Percent thresholds (`unit: percent`) compare the count as a percentage
  of data rows: `multiply( divide( @c, subtract(total_lines(), 1) ), 100 )`.
  For a percent rule only `mustBe: 0` and `mustBeLessOrEqualTo: 0` are
  zero tolerance; fewer than 1 percent is not the same as none.

Library metrics

- `rowCount` (schema level): checked on `subtract(total_lines(), 1)`.
- `invalidValues` (property): `arguments.validValues` -> `in()`,
  `arguments.pattern` -> `regex()`, both -> `and()`. The counter counts
  non-empty values that break the rule; empty values are
  `nullValues`/`missingValues`, not `invalidValues`.
- `nullValues` (property): any threshold makes the column `.notnone`, so
  lines with a null do not match; a non-zero threshold also counts
  `empty.nocontrib(#c)`.
- `missingValues` (property): `arguments.missingValues` lists what counts
  as missing; with no arguments, null or empty. Null or `""` in the list
  makes the column `.notnone`; other values become `not( in(#c, "...") )`.
  A non-zero threshold counts both kinds.
- `duplicateValues` (property): makes the column unique (see `unique`
  above). A non-zero threshold also counts `has_dups(#c)`, ignoring
  empties on an optional column.
- `duplicateValues` (schema level, `arguments.properties`): the
  combination of columns must be unique: `not( has_dups(#a, #b) )`. A row
  with an empty value in an optional column of the combination is never a
  duplicate. A non-zero threshold also counts. The check follows the
  per-column checks; an unknown property name is reported.
- v3.0's deprecated `rule` key is read the same as `metric`.

Allowed values

- Both forms are supported: the v3.2.0 property `enum` (EnumValue objects,
  `- value: open`, or plain values), and the v3.0/v3.1 property quality
  rule `metric: invalidValues` with `arguments.validValues`.
- Values become `in()`'s pipe-delimited string. A value containing `|` or
  `"` cannot be expressed; the whole value list is reported.
- `null` and `""` in an allowed-values list are dropped: empty values are
  governed by required/optional, not by the list. A list of only empty
  values is reported.

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
- Still reported, not translated: percent `rowCount` (no meaning), and
  non-integer `multipleOf`.
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
  `unique` on an optional date is checked like any optional unique column.
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
