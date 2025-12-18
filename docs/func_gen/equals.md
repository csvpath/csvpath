
## equals()
Equals

Tests the equality of two values.

In most cases you will use == to test equality. However, in some cases
equals() gives more flexibility.

Moreover, in one case, you must use the function, not ==. Using
equals() is required in order to set a variable to the value of an
equality test.

In other words, to set @a equal to the equality test of @b to the
string "c", you must do: @a = equals(@b, "c"). @a = @b == "c" is not
allowed.

| Data signatures                            |
|:-------------------------------------------|
| equals( is this: Any, equal to that: Any ) |

| Call signatures                                                                                                                    |
|:-----------------------------------------------------------------------------------------------------------------------------------|
| equals( is this: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, equal to that: Term ǁ Variable ǁ Header ǁ Function ǁ Reference ) |

| Purpose    | Value                              |
|:-----------|:-----------------------------------|
| Main focus | equals() determines if lines match |
| Aliases    | equal, equals, eq                  |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


