
## counter()

Increments a variable. The increment is 1 by default.

Counters must be named using a name qualifier. Without that, the ID
generated for your counter will be tough to use.

A name qualifier is an arbitrary name added with a dot after the
function name and before the parentheses. It looks like
counter.my_name()

| Data signatures                                             |
|:------------------------------------------------------------|
| counter( [amount to increment by: $${\color{green}int}$$] ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| counter( [amount to increment by: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ǁ Equality] ) |

| Purpose    | Value                                 |
|:-----------|:--------------------------------------|
| Main focus | counter() produces a calculated value |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Name qualifier   | optionally expected                                                                |


