
# Mismatch

`mismatch()` returns the number of headers in a row greater or less than the number expected.

CsvPath uses the 0th row as headers. Headers are like columns, except without any of the guarintees you might wish for:
- The expected headers may not have delimited "slots" or "cells" in any given line
- The number of headers per file is not fixed
- There can be multiple header rows, not just the first non-blank line
- Some lines can be blank and have no "cells" so no headers apply

When the designated headers -- usually those set from the first non-blank line -- do not match the number of values in a row there is a mismatch. The number of values means data values plus the empty string for those values that have a position in the line but no more substantial content.

`mismatch()` counts the number of values, including blanks, compares that number to the number of headers, and returns the difference as a positive or signed integer. By default `mismatch()` returns the absolute value of the difference. If you pass a negative boolean (including `"false"`) or `"signed"` then the number `mismatch()` returns will be negative if the line has fewer delimited values than the current headers.

If a line has no delimiters but does have whitespace characters it technically has one header. `mismatch()` doesn't give credit for the whitespace because in reality the line is blank and has zero headers.

## Examples

```bash
    $[1*][
        ~ track the mismatched lines in the CSV file using a stack.
          at the same time, track the mismatch counts in a
          parallel stack so we know where the biggest problems are
        ~
            push("mismatch", mismatch() )
            mismatch() -> push("mismatched_lines", count_lines() )
```

This path simply tracks mismatches.

```bash
    gt(mismatch("signed"), 9) ->
            skip(
                reset_headers(
                    print("Headers increased.
                           Resetting to $.csvpath.headers.")))
```

Here we are looking for only positive changes, not a negative ones, so we pass `signed`. When a positive change is found the headers are reset to the values of the current line.



