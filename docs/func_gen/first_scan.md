
## first_scan()

Evaluates to True on the first line scanned. A scanned line is one
that has been evaluated for matching.

Optionally, takes a function argument that is evaluated if firstscan()
matches

| Data signatures                                                             |
|:----------------------------------------------------------------------------|
| first_scan( [eval this: $${\color{green}None}$$ ǁ $${\color{green}Any}$$] ) |

| Call signatures                                                                                                          |
|:-------------------------------------------------------------------------------------------------------------------------|
| first_scan( [eval this: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ Equality] ) |

| Purpose    | Value                                  |
|:-----------|:---------------------------------------|
| Main focus | first_scan() determines if lines match |
| Aliases    | firstscan, first_scan                  |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


