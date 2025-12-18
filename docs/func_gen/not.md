
## not()

not() returns the boolean inverse of its argument.

Optionally, if an function is provided as a second argument, not()
will evaluate it as a side-effect if not() evaluates to True.

| Data signatures                                                                          |
|:-----------------------------------------------------------------------------------------|
| not( value applied to: None ǁ Any, [A function to invoke if not() is True: None ǁ Any] ) |

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| not( value applied to: [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function) ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ǁ Equality, [A function to invoke if not() is True: [Function](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#function)] ) |

| Purpose    | Value                           |
|:-----------|:--------------------------------|
| Main focus | not() determines if lines match |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


