
## interpolate()

Uses the Python string formatting mini language.

E.g. to format a float to having two decimal places use a format
argument of “:.2f”

Interpolates a complete Pythonic formatting string with one
replacement value.                 Use {{ and }} to demarcate your
replacement pattern.

| Data signatures                               |
|:----------------------------------------------|
| interpolate( value: None ǁ Any, format: str ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| interpolate( value: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ Function ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), format: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ Function ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ) |

| Purpose    | Value                                     |
|:-----------|:------------------------------------------|
| Main focus | interpolate() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


