
In

in() checks if the component value is in the values of the other
arguments.

One advanced in() capability is for lookups in the results of other
named-path group runs.

String terms are treated as possibly | delimited strings of values

| Data signatures                                                 |
|:----------------------------------------------------------------|
| in( Value to find: None ǁ Any, Place to look: None ǁ Any, ... ) |

| Call signatures                                                                                                                           |
|:------------------------------------------------------------------------------------------------------------------------------------------|
| in( Value to find: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, Place to look: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, ... ) |

| Purpose    | Value                          |
|:-----------|:-------------------------------|
| Main focus | in() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


