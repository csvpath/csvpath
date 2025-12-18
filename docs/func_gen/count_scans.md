
## count_scans()

Returns the current number of lines that have been scanned.

Scanning predicts a specific number of lines for a given file.
However, if a line is expected to be scanned but is skipped because it
is blank it is not counted as scanned.

For example, a scanning instruction [1-3] indicates that lines 1, 2,
and 3 would be scanned. But if line 2 is blank and we are configured
to skip blank lines (the default), when we're done scanning we will
have a count_scans() total of 2, not 3, because we skipped a blank
line.

| Purpose    | Value                                     |
|:-----------|:------------------------------------------|
| Main focus | count_scans() produces a calculated value |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
