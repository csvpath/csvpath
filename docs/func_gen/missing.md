
Missing

Tests if any contained or referenced match components evaluate to
False. If missing() has no arguments, check if any headers are empty
or missing.

| Data signatures                                                   |
|:------------------------------------------------------------------|
| missing()                                                         |
| missing( [a function indicating all headers or all variables: ] ) |
| missing( [one of a set of match components: NoneǁAny], ... )      |

| Call signatures                                                                    |
|:-----------------------------------------------------------------------------------|
| missing()                                                                          |
| missing( [a function indicating all headers or all variables: VariablesǁHeaders] ) |
| missing( [one of a set of match components: FunctionǁVariableǁHeader], ... )       |

| Purpose    | Value                               |
|:-----------|:------------------------------------|
| Main focus | missing() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


