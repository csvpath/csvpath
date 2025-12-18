Percent unique
Returns the percent of values of a header that are unique over the
lines seen so far.

Uses a percent_unique variable behind the scenes. Add a name qualifier
to allow for more than one percent unique function.
| Data signatures                        |
|:---------------------------------------|
| percent_unique( header to watch: [36m[3mstr[0m ) |
| Call signatures                           |
|:------------------------------------------|
| percent_unique( header to watch: [36m[3mHeader[0m ) |
| Purpose    | Value                                        |
|:-----------|:---------------------------------------------|
| Main focus | percent_unique() produces a calculated value |
| Context          | Qualifier           |
|:-----------------|:--------------------|
| Match qualifiers | [36m[3monmatch[0m             |
| Value qualifiers | [36m[3monmatch[0m             |
| Name qualifier   | [36m[3moptionally expected[0m |
