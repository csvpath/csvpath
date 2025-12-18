
Not equal to

Tests the equality of two values.

In most cases you will use == to test equality. However, in some cases
not_equal_to() gives more flexibility.

Moreover, in one case, you must use the function, not ==. Using
not_equal_to() is required in order to set a variable to the value of
an equality test.

In other words, to set @a equal to the equality test of @b to the
string "c", you must do: @a = not_equal_to(@b, "c"). @a = @b == "c" is
not allowed.

| Data signatures                                  |
|:-------------------------------------------------|
| not_equal_to( is this: Any, equal to that: Any ) |

| Call signatures                                                                                                          |
|:-------------------------------------------------------------------------------------------------------------------------|
| not_equal_to( is this: TermǁVariableǁHeaderǁFunctionǁReference, equal to that: TermǁVariableǁHeaderǁFunctionǁReference ) |

| Purpose    | Value                                    |
|:-----------|:-----------------------------------------|
| Main focus | not_equal_to() determines if lines match |
| Aliases    | neq, not_equal_to                        |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


