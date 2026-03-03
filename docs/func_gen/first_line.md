
## first_line()

Evaluates to True on the first line of the file. If the first line is
blank and blanks are skipped firstline() never fires.

Optionally, takes a function argument that is evaluated if firstline()
matches

| Data signatures                                                             |
|:----------------------------------------------------------------------------|
| first_line( [eval this: $${\color{green}None}$$ ǁ $${\color{green}Any}$$] ) |

| Call signatures                                                                                                          |
|:-------------------------------------------------------------------------------------------------------------------------|
| first_line( [eval this: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ Equality] ) |

| Purpose    | Value                                  |
|:-----------|:---------------------------------------|
| Main focus | first_line() determines if lines match |
| Aliases    | firstline, first_line                  |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


[[Back to index](https://github.com/csvpath/csvpath/blob/main/docs/func_gen/index.md)]
