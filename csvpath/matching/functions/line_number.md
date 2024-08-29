
# Line Number

`line_number()` returns the physical index of the line that is currently being considered. It includes blank lines, lines that have delimiters but no values, unscanned lines, etc. If you look at the lines in a CSV as being in a list, `line_number()` is the index of your current line.

The topic of counts vs. pointers is more interesting than you might think. At a high level, a count is a 1-based experience and a pointer is a 0-based location. CsvPath naming is to use `count` for counting and `number` for pointing.

## Examples

```bash
    $[*][ mismatch() -> push("mismatched lines", line_number()) ]
```
This path captures the line numbers of lines that have less or more delimited values than the headers. E.g., say we have a 5-line file named orders.csv. Orders.csv has 3 headers:

```csv
Date,City,Order Number
```

And it has 1 header line, 4 data lines, and a blank line:

```csv
Date,City,Order Number
2024-01-01,New York, 0390312
2024-01-01,Phoenix
2024-01-01,Tampa, 0358319, 0347832

2024-01-01,Boston, 0344764
```

The result would be that our `mismatched lines` variable would have `[2, 3, 4]`. By contrast,

```bash
    $[*][ mismatch() -> push("mismatched lines", count_lines())
```

Would result in `mismatched lines` equaling `[3, 4]`.

The reason is that the csvpath saw the first mismatch on the third line it saw, and the fourth right after it. By default CsvPath skips blank lines, so there is no third mismatch from the perspective of `count_lines()` because that line was never seen by that function. You can't count what you can't see.

