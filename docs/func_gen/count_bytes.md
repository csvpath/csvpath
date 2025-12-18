
## count_bytes()

Returns the total data bytes written count.

This function is only for named-path group runs. Individual CsvPath
instances do not write out data, so this value would be 0 for them.

| Purpose    | Value                                     |
|:-----------|:------------------------------------------|
| Main focus | count_bytes() produces a calculated value |

| Context          | Qualifier                                                                          |
|:-----------------|:-----------------------------------------------------------------------------------|
| Match qualifiers | [onmatch](https://github.com/csvpath/csvpath/blob/main/docs/qualifiers.md#onmatch) |
| Value qualifiers | onmatch                                                                            |


