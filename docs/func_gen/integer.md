
## integer()

integer() is a type function often used as an argument to line().

It indicates that the value it receives must be an integer.

| Data signatures                                                                           |
|:------------------------------------------------------------------------------------------|
| integer( header: None ǁ str ǁ int, [max: None ǁ float ǁ int], [min: None ǁ float ǁ int] ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| integer( header: [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), [max: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable)], [min: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable)] ) |

| Purpose    | Value                               |
|:-----------|:------------------------------------|
| Main focus | integer() determines if lines match |
| Type       | Integer is a line() schema type     |

| Context          | Qualifier                          |
|:-----------------|:-----------------------------------|
| Match qualifiers | onmatch, notnone, strict, distinct |
| Value qualifiers | onmatch, notnone, strict           |


