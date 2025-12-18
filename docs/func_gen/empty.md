
## empty()

empty() checks for empty or blank header values in a given line. It
reports True only if all the places it is directed to look are empty.

If you pass it a headers() function it checks for all headers being
empty.

| Data signatures                                                                    |
|:-----------------------------------------------------------------------------------|
| empty( Points to the headers: )                                                    |
| empty( Component to check: $${\color{green}None}$$ ǁ $${\color{green}Any}$$, ... ) |

| Call signatures                                                                                                                                                                                                                                                                            |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| empty( Points to the headers: Headers )                                                                                                                                                                                                                                                    |
| empty( Component to check: [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header), ... ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | empty() determines if lines match |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


