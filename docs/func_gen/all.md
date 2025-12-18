
## all()

Tests if all contained or referenced match components evaluate to
True. If all() has no arguments the check is if all headers have
values.

| Data signatures                                                                                  |
|:-------------------------------------------------------------------------------------------------|
| all()                                                                                            |
| all( [a function indicating all headers or all variables: ] )                                    |
| all( [one of a set of match components: $${\color{green}None}$$ ǁ $${\color{green}Any}$$], ... ) |

| Call signatures                                                                                                                                                                                                                                                                                          |
|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| all()                                                                                                                                                                                                                                                                                                    |
| all( [a function indicating all headers or all variables: Variables ǁ Headers] )                                                                                                                                                                                                                         |
| all( [one of a set of match components: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header)], ... ) |

| Purpose    | Value                           |
|:-----------|:--------------------------------|
| Main focus | all() determines if lines match |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |


