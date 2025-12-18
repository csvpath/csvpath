
## not()
Not

not() returns the boolean inverse of its argument.

Optionally, if an function is provided as a second argument, not()
will evaluate it as a side-effect if not() evaluates to True.

| Data signatures                                                                          |
|:-----------------------------------------------------------------------------------------|
| not( value applied to: None ǁ Any, [A function to invoke if not() is True: None ǁ Any] ) |

| Call signatures                                                                                                                 |
|:--------------------------------------------------------------------------------------------------------------------------------|
| not( value applied to: Variable ǁ Header ǁ Function ǁ Reference ǁ Equality, [A function to invoke if not() is True: Function] ) |

| Purpose    | Value                           |
|:-----------|:--------------------------------|
| Main focus | not() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


