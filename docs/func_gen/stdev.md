
## stdev()

Given a stack of values returns the sample standard deviation.

This function expects a string naming a stack prepared by the csvpath
holding the values to be assessed. The stack variable can be created
using push() or other functions.

| Data signatures                             |
|:--------------------------------------------|
| stdev( stack var name: str ǁ tuple ǁ list ) |

| Call signatures                                                                                                                                                                                     |
|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| stdev( stack var name: [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ Function ǁ [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ) |

| Purpose    | Value                               |
|:-----------|:------------------------------------|
| Main focus | stdev() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


