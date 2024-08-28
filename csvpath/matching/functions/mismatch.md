
# Mismatch

`mismatch()` returns the number of headers in a row greater or less than the number expected.

CsvPath uses the 0th row as headers. Headers are like columns, except without any of the guarintees you might wish for:
- The expected headers may not have "slots" or "cells" in any given row
- The number of headers per file is not fixed
- There can be multiple header rows, not just the first non-blank line
- Some lines can be blank and have no "cells" so no headers apply

When the designated headers -- usually those set from the first non-blank line -- do not match the number of values in a row there is a mismatch. The number of values means data values plus the empty string for those values that have a position in the line but no more substantial content.

`mismatch()` counts the number of values, including blanks, compares that number to the number of headers, and returns the difference as a positive integer.

## Examples

```bash
    $[1*][
        ~ track the mismatched lines in the CSV file using a stack.
          at the same time, track the mismatch counts in a
          parallel stack so we know where the biggest problems are
        ~
        or(
            push("mismatch", mismatch() )
            mismatch() -> push("mismatched_lines", count_lines() )
        ) -> fail_and_stop()
```


