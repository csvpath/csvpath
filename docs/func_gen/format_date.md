
## format_date()

Outputs a date or datetime as a string using strftime formatting.
If a date format does not include date parts a match error is raised.

| Data signatures                                          |
|:---------------------------------------------------------|
| format_date( date: None ǁ date ǁ datetime, format: str ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| format_date( date: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ Function ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), format: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ Function ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ) |

| Purpose    | Value                                     |
|:-----------|:------------------------------------------|
| Main focus | format_date() produces a calculated value |

| Context          | Qualifier        |
|:-----------------|:-----------------|
| Match qualifiers | onmatch          |
| Value qualifiers | onmatch, notnone |


