
## all()
All

Tests if all contained or referenced match components evaluate to
True. If all() has no arguments the check is if all headers have
values.

| Data signatures                                               |
|:--------------------------------------------------------------|
| all()                                                         |
| all( [a function indicating all headers or all variables: ] ) |
| all( [one of a set of match components: None ǁ Any], ... )    |

| Call signatures                                                                  |
|:---------------------------------------------------------------------------------|
| all()                                                                            |
| all( [a function indicating all headers or all variables: Variables ǁ Headers] ) |
| all( [one of a set of match components: Function ǁ Variable ǁ Header], ... )     |

| Purpose    | Value                           |
|:-----------|:--------------------------------|
| Main focus | all() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


