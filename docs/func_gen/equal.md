
Equal

Tests the equality of two values.

In most cases you will use == to test equality. However, in some cases
equal() gives more flexibility.

Moreover, in one case, you must use the function, not ==. Using
equal() is required in order to set a variable to the value of an
equality test.

In other words, to set @a equal to the equality test of @b to the
string "c", you must do: @a = equal(@b, "c"). @a = @b == "c" is not
allowed.

| Data signatures                           |
|:------------------------------------------|
| equal( is this: Any, equal to that: Any ) |

| Call signatures                                                                                                   |
|:------------------------------------------------------------------------------------------------------------------|
| equal( is this: TermǁVariableǁHeaderǁFunctionǁReference, equal to that: TermǁVariableǁHeaderǁFunctionǁReference ) |

| Purpose    | Value                             |
|:-----------|:----------------------------------|
| Main focus | equal() determines if lines match |
| Aliases    | equal, equals, eq                 |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


