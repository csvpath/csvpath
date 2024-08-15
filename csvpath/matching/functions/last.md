
# First and Last Functions

## last()
Returns True to `matches()` when the current row is the last row in the file or the last row to be scanned.

## firstline(), firstscan(), firstmatch()
- `firstline()` is True only for the 0th row; the headers row. If the scan does not start at 0 `firstline()` will not be seen.
- `firstscan()` is True on the first line scanned. When the scan starts at 0 `firstscan()` equals `firstline()`.
- `firstmatch()` is True on the first row where all other match components are True

## `nocontrib`
In many cases you will want to qualify these functions with the `nocontrib` qualifier. `nocontrib` indicates that the function isn't considered for matching. If you don't use `nocontrib` you will get at most 1 match.

## Example

    $file.csv[*][print(last(), "the file has $.line_count rows")]




