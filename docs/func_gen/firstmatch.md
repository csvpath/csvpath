
## firstmatch()

Evaluates to True at the first line matched. firstmatch() implies the
onmatch qualifier, but does not require it.

Optionally, takes a function argument that is evaluated if
firstmatch() matches

| Data signatures                       |
|:--------------------------------------|
| firstmatch( [eval this: None ǁ Any] ) |

| Call signatures                                                                                                          |
|:-------------------------------------------------------------------------------------------------------------------------|
| firstmatch( [eval this: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ Equality] ) |

| Purpose    | Value                                  |
|:-----------|:---------------------------------------|
| Main focus | firstmatch() determines if lines match |
| Aliases    | firstmatch, first_match                |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


