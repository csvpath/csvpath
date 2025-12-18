
## line_before()

Tracks the most recent value of a header to enable comparison with the
current value.

| Data signatures                                    |
|:---------------------------------------------------|
| line_before( header name: $${\color{green}str}$$ ) |
| line_before( header: $${\color{green}Any}$$ )      |

| Call signatures                                                                                        |
|:-------------------------------------------------------------------------------------------------------|
| line_before( header name: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ) |
| line_before( header: [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) )  |

| Purpose    | Value                                     |
|:-----------|:------------------------------------------|
| Main focus | line_before() produces a calculated value |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | onmatch                                                                            |
| Name qualifier   | optionally expected                                                                |


