
## in()

in() checks if the component value is in the values of the other
arguments.

One advanced in() capability is for lookups in the results of other
named-path group runs.

String terms are treated as possibly | delimited strings of values

| Data signatures                                                 |
|:----------------------------------------------------------------|
| in( Value to find: None ǁ Any, Place to look: None ǁ Any, ... ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| in( Value to find: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), Place to look: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), ... ) |

| Purpose    | Value                          |
|:-----------|:-------------------------------|
| Main focus | in() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


