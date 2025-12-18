
## roll()

Rolls a date or datetime forward or backwards by a number of units.

The units accepted are: seconds, minutes, hours, days, months, years.
Both singular and plural forms are accepted.

| Data signatures                                                |
|:---------------------------------------------------------------|
| roll( date: None ǁ date ǁ datetime, how_many: int, unit: str ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| roll( date: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), how_many: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ǁ [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term), unit: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ) |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | roll() produces a calculated value |

| Context          | Qualifier        |
|:-----------------|:-----------------|
| Match qualifiers | onmatch          |
| Value qualifiers | onmatch, notnone |


