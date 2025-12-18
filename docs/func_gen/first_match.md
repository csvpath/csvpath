
First match

Evaluates to True at the first line matched. firstmatch() implies the
onmatch qualifier, but does not require it.

Optionally, takes a function argument that is evaluated if
firstmatch() matches

| Data signatures                      |
|:-------------------------------------|
| first_match( [eval this: None|Any] ) |

| Call signatures                               |
|:----------------------------------------------|
| first_match( [eval this: Function|Equality] ) |

| Purpose    | Value                                   |
|:-----------|:----------------------------------------|
| Main focus | first_match() determines if lines match |
| Aliases    | firstmatch, first_match                 |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


