
## size()

Returns number of values in a stack variable.

Unless the notnone qualifier is present, the stack is created if not
found.

| Data signatures                    |
|:-----------------------------------|
| size( stack name: str )            |
| size( stack: list ǁ tuple ǁ None ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                        |
|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| size( stack name: [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ Function ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ǁ [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ) |
| size( stack: [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ Function ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) )                                                                                                                                                                    |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | size() produces a calculated value |
| Aliases    | peek_size, size                    |

| Context          | Qualifier        |
|:-----------------|:-----------------|
| Match qualifiers | onmatch          |
| Value qualifiers | onmatch, notnone |


