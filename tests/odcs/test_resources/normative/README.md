# ODCS -> CsvPath normative pairs

Each subdirectory is one normative pair: an ODCS contract and the csvpath(s)
the converter must produce from it, plus data that proves the expected
csvpaths behave as intended. `tests/odcs/test_odcs_normative_pairs.py`
verifies the pairs themselves; converter tests develop against them.

Layout of a pair:

    contract.yaml        ODCS input; must validate against the official
                         JSON Schema for its apiVersion (see ../schema/)
    expected/*.csvpath   converter output, one csvpath per schema object
    data/*.csv           sample data, conforming and non-conforming lines
    expected.yaml        per run: csvpath, data file, valid_lines, is_valid

## Conversion decisions (agreed with David, 2026-10-09)

Scope and shape

- ODCS -> CsvPath only, for now. CsvPath -> ODCS is later, if at all.
- Supported apiVersions: v3.0.x, v3.1.0, v3.2.0. v2.x is rejected.
- One schema object (one table) becomes one csvpath. Grouping csvpaths into
  named-paths groups is a later stage in the main codebase, not here.
- The generated csvpath has no filename in its root (`$[...]`), as for any
  csvpath loaded into a named-paths group.

Matching and validation semantics

- The csvpath matches valid (conforming) lines.
- Every generated csvpath carries
  `validation-mode: print, no-raise, no-fail, no-stop` in its metadata
  comment. Users edit that to change behavior.
- Properties map to `line()` wherever practical, trusting ODCS property
  order as column order. `line()` reads like SQL DDL, which keeps the
  cognitive load low for people new to CsvPath.
- Header name is `physicalName` when present, else `name`.

File-level checks

- File-level rules (e.g. `rowCount`) report through `fail()` and the
  csvpath's `is_valid`, not through matching.
- They need a `$[*]` scan, because with `$[1*]` a header-only file never
  reaches `last()`. Only csvpaths with file-level checks use this form;
  all others use the simpler `$[1*]`:

      $[*][
          and.nocontrib( last(), not( gt( subtract(total_lines(), 1), 0 ) ) ) -> fail()
          first_line.nocontrib() -> skip()
          line( ... )
      ]

Quality rules with thresholds

- A zero threshold (`mustBe: 0` and equivalents) is a per-line constraint:
  offending lines do not match.
- A non-zero threshold (e.g. `mustBeLessThan: 5`, or a percent `unit`) does
  both: offending lines do not match, AND a file-level count is checked at
  the last line with `fail()`. The run continues collecting matching lines;
  it does not stop.

Allowed values

- Both forms are supported: the v3.2.0 property `enum` (EnumValue objects,
  `- value: open`), and the v3.0/v3.1 property quality rule
  `metric: invalidValues` with `arguments.validValues`.

Known framework issue

- `date()`/`datetime()` inside `line()` reject empty values even without
  `notnone` (issue #300). Until fixed, optional dates are emitted as
  `blank(#d)` in the `line()` plus `or( empty(#d), date(#d, "<fmt>") )`.
  Required dates use `date.notnone(#d, "<fmt>")` in the `line()` directly.

Regular expressions

- ODCS patterns (ECMA-262) become CsvPath `/.../` regex literals, run by
  Python `re`. Unescaped `/` in a pattern is escaped. ECMA-only constructs
  that cannot carry over are reported, not translated.
- The regex goes in the first argument of `regex()`, so a data value that
  begins with `/` cannot be mistaken for the regex.
