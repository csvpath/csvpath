
## missing()

Tests if any contained or referenced match components evaluate to
False. If missing() has no arguments, check if any headers are empty
or missing.

| Data signatures                                                                                      |
|:-----------------------------------------------------------------------------------------------------|
| missing()                                                                                            |
| missing( [a function indicating all headers or all variables: ] )                                    |
| missing( [one of a set of match components: $${\color{green}None}$$ ǁ $${\color{green}Any}$$], ... ) |

| Call signatures                                                                                                                                                                                                                                                                                              |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| missing()                                                                                                                                                                                                                                                                                                    |
| missing( [a function indicating all headers or all variables: Variables ǁ Headers] )                                                                                                                                                                                                                         |
| missing( [one of a set of match components: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header)], ... ) |

| Purpose    | Value                               |
|:-----------|:------------------------------------|
| Main focus | missing() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


