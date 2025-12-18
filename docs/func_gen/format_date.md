
Format date

Outputs a date or datetime as a string using strftime formatting.
If a date format does not include date parts a match error is raised.

| Data signatures                                      |
|:-----------------------------------------------------|
| format_date( date: None|date|datetime, format: str ) |

| Call signatures                                                                                     |
|:----------------------------------------------------------------------------------------------------|
| format_date( date: Term|Function|Header|Variable|Reference, format: Term|Function|Header|Variable ) |

| Purpose    | Value                                     |
|:-----------|:------------------------------------------|
| Main focus | format_date() produces a calculated value |

| Context          | Qualifier        |
|:-----------------|:-----------------|
| Match qualifiers | onmatch          |
| Value qualifiers | onmatch, notnone |


