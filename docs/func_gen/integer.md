
Integer

integer() is a type function often used as an argument to line().

It indicates that the value it receives must be an integer.

| Data signatures                                                               |
|:------------------------------------------------------------------------------|
| integer( header: Noneǁstrǁint, [max: Noneǁfloatǁint], [min: Noneǁfloatǁint] ) |

| Call signatures                                                                                                     |
|:--------------------------------------------------------------------------------------------------------------------|
| integer( header: HeaderǁVariableǁFunctionǁReference, [max: TermǁFunctionǁVariable], [min: TermǁFunctionǁVariable] ) |

| Purpose    | Value                               |
|:-----------|:------------------------------------|
| Main focus | integer() determines if lines match |
| Type       | Integer is a line() schema type     |

| Context          | Qualifier                          |
|:-----------------|:-----------------------------------|
| Match qualifiers | onmatch, notnone, strict, distinct |
| Value qualifiers | onmatch, notnone, strict           |


