
## peek_size()

Returns number of values in a stack variable.

Unless the notnone qualifier is present, the stack is created if not
found.

| Data signatures                                            |
|:-----------------------------------------------------------|
| peek_size( stack name: $${\color{green}str}$$ )            |
| peek_size( stack: list ǁ tuple ǁ $${\color{green}None}$$ ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| peek_size( stack name: [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ǁ [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ) |
| peek_size( stack: [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) )                                                                                                                                                                    |

| Purpose    | Value                                   |
|:-----------|:----------------------------------------|
| Main focus | peek_size() produces a calculated value |
| Aliases    | peek_size, size                         |

| Context          | Qualifier        |
|:-----------------|:-----------------|
| Match qualifiers | onmatch          |
| Value qualifiers | onmatch, notnone |


