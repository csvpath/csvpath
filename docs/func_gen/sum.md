
## sum()

Sum

Returns the running sum of a source.

sum() is similar to subtotal() but unlike subtotal it does not use
categorization to create multiple running totals.

Remember that CsvPath Language will convert None, bool, and the empty
string to int. This results in a predictable summation. If you are
looking for a way to make sure all lines have summable values try
using integer() or another approach.

| Data signatures                                                    |
|:-------------------------------------------------------------------|
| sum( sum this: $${\color{green}int}$$ ǁ $${\color{green}float}$$ ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                        |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| sum( sum this: [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | sum() produces a calculated value |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | onmatch                                                                            |
| Name qualifier   | optionally expected                                                                |


