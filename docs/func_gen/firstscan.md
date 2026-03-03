
## firstscan()

Evaluates to True on the first line scanned. A scanned line is one
that has been selected for matching.

firstscan() is basically the first data line. If you select all lines
for scanning but the first three are skipped for being blank,
firstscan()'s first line is line #3; whereas, in that situation
firstline() never fires because the first line is blank. (Remember
that the line number is 0-based)

Optionally, takes a function argument that is evaluated if firstscan()
matches

| Data signatures                                                            |
|:---------------------------------------------------------------------------|
| firstscan( [eval this: $${\color{green}None}$$ ǁ $${\color{green}Any}$$] ) |

| Call signatures                                                                                                         |
|:------------------------------------------------------------------------------------------------------------------------|
| firstscan( [eval this: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ Equality] ) |

| Purpose    | Value                                 |
|:-----------|:--------------------------------------|
| Main focus | firstscan() determines if lines match |
| Aliases    | firstscan, first_scan                 |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
