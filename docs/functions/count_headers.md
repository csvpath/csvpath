
# Count Headers

`count_headers()` and `count_headers_in_line()` are simple but need to be understood.

- `count_headers()` returns the number of headers in the headers row (the 0th row)
- `count_headers_in_line()` counts the number of headers in the current row.

In a CSV file there is an expected number of columns defined by the header row and/or the general number of columns in rows. However, many CSV files have rows where the number of values is smaller or larger than in the 0th row or the typical line anywhere in the file.

CsvPath uses the word "header" more than column. Saying a CSV file has columns makes it feel like a CSV file has a format and rigour on par with a relational database. The need for `count_headers_in_line()` makes the point that it doesn't. We can't count line values and we can't rely on all lines having all headers. And as long as the data stays in CSV, we certainly don't have columns in a spreadsheet or RDBMS sense.

## Examples

```bash
    ${PATH}[*]
    [
        gt(count_headers_in_line(),  count_headers()) -> @toomany = count_lines()
        lt(count_headers_in_line(),  count_headers()) -> @toofew = count_lines()
        @toofew -> fail_and_stop()
    ]
```

This csvpath checks for lines with too many or too few headers. When it sees one with too few it declares the file invalid and stops processing.


