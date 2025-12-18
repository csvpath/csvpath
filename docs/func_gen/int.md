
Int

Casts a value to an int.

Note that the actuals in the data signatures are types that the value
must convert to. A bool True would convert to 1 and would therefore be
castable using this function.

| Data signatures                  |
|:---------------------------------|
| int( cast this: Noneǁintǁfloat ) |

| Call signatures                                 |
|:------------------------------------------------|
| int( cast this: TermǁVariableǁHeaderǁFunction ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | int() produces a calculated value |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


