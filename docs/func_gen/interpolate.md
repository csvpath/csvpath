
Interpolate

Uses the Python string formatting mini language.

E.g. to format a float to having two decimal places use a format
argument of “:.2f”

Interpolates a complete Pythonic formatting string with one
replacement value.                 Use {{ and }} to demarcate your
replacement pattern.

| Data signatures                             |
|:--------------------------------------------|
| interpolate( value: None|Any, format: str ) |

| Call signatures                                                                                                |
|:---------------------------------------------------------------------------------------------------------------|
| interpolate( value: Term|Function|Header|Variable|Reference, format: Term|Function|Header|Variable|Reference ) |

| Purpose    | Value                                     |
|:-----------|:------------------------------------------|
| Main focus | interpolate() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


