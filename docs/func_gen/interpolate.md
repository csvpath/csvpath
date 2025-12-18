
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

| Call signatures                                                                                                                |
|:-------------------------------------------------------------------------------------------------------------------------------|
| interpolate( value: Term ǁ Function ǁ Header ǁ Variable ǁ Reference, format: Term ǁ Function ǁ Header ǁ Variable ǁ Reference ) |

| Purpose    | Value                                     |
|:-----------|:------------------------------------------|
| Main focus | interpolate() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


