
# First and Last Functions

## last()
Matches when the current row is the last row in the file and/or the last row to be scanned.

## firstline(), firstscan(), firstmatch()
- `firstline()` is True only for the 0th row; the headers row. If the scan does not start at 0 `firstline()` will not be seen.
- `firstscan()` is True on the first line scanned. When the scan starts at 0 `firstscan()` equals `firstline()`.
- `firstmatch()` is True on the first row where all other match components are True

## nocontrib
In many cases you will want to qualify these functions with the `nocontrib` qualifier. `nocontrib` indicates that the function isn't considered for matching. If you don't use `nocontrib` you will get at most 1 match.

## Example

```bash
    $file.csv[*][
            firstscan.nocontrib() -> print("we're scanning the whole file from the 0th line")
            last.nocontrib() -> print("the file has $.count_lines rows")]
```

This csvpath prints a message at the beginning and end of its scan. It collects all the rows. If we remove one of the `nocontrib` we collect just that line. If we remove both of them we collect nothing. Either way, the messages are still printed.


