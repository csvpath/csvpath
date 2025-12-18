
In

in() checks if the component value is in the values of the other
arguments.

One advanced in() capability is for lookups in the results of other
named-path group runs.

String terms are treated as possibly | delimited strings of values

| Data signatures                                             |
|:------------------------------------------------------------|
| in( Value to find: NoneǁAny, Place to look: NoneǁAny, ... ) |

| Call signatures                                                                                                           |
|:--------------------------------------------------------------------------------------------------------------------------|
| in( Value to find: TermǁVariableǁHeaderǁFunctionǁReference, Place to look: TermǁVariableǁHeaderǁFunctionǁReference, ... ) |

| Purpose    | Value                          |
|:-----------|:-------------------------------|
| Main focus | in() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


