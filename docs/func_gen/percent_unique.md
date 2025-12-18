
## percent_unique()
Percent unique

Returns the percent of values of a header that are unique over the
lines seen so far.

Uses a percent_unique variable behind the scenes. Add a name qualifier
to allow for more than one percent unique function.

| Data signatures                        |
|:---------------------------------------|
| percent_unique( header to watch: str ) |

| Call signatures                           |
|:------------------------------------------|
| percent_unique( header to watch: Header ) |

| Purpose    | Value                                        |
|:-----------|:---------------------------------------------|
| Main focus | percent_unique() produces a calculated value |

| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | onmatch             |
| Value qualifiers | onmatch             |
| Name qualifier   | optionally expected |


