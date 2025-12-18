
In

in() checks if the component value is in the values of the other
arguments.

One advanced in() capability is for lookups in the results of other
named-path group runs.

String terms are treated as possibly | delimited strings of values

| Data signatures                                             |
|:------------------------------------------------------------|
| in( Value to find: None|Any, Place to look: None|Any, ... ) |

| Call signatures                                                                                                           |
|:--------------------------------------------------------------------------------------------------------------------------|
| in( Value to find: Term|Variable|Header|Function|Reference, Place to look: Term|Variable|Header|Function|Reference, ... ) |

| Purpose    | Value                          |
|:-----------|:-------------------------------|
| Main focus | in() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


