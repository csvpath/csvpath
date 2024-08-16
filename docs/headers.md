
# Headers

Headers identify columns. In general, in CsvPath "column" and "header" are synonymous.

A header is identified by a `#` followed by a name or integer. The header references the value at a column within the row being matched.

Names of headers are whatever is found in line 0, the header row. If a header contains a space char it must be quoted. Files that don't intrinsically have headers, still can use headers to refer to columns in csvpaths.

A numbered header references a column by its 0-based column index. The last column can be referenced by the `end()` function.

The name of a header can be found using the `column()` function, as in:

```bash
    $file.csv[*][ @col = column(3) print("the header you need is named: #$.variables.col")]
```

As another example, the name of the second to last column can be found using `column(minus(1))`.

Header values can be tested as a boolean (a Python bool) with the `asbool` qualifier. <a href='https://github.com/dk107dk/csvpath/blob/main/docs/qualifiers.md'>Read about qualifiers here.</a>

# Examples

- `#0`
- `#firstname`
- `#"All Firstnames"`
- `end()`
- `#senior.asbool`

All of these point to some value in a row or to a blank column.


