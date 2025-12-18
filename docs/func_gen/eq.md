
## eq()
Eq

Tests the equality of two values.

In most cases you will use == to test equality. However, in some cases
eq() gives more flexibility.

Moreover, in one case, you must use the function, not ==. Using eq()
is required in order to set a variable to the value of an equality
test.

In other words, to set @a equal to the equality test of @b to the
string "c", you must do: @a = eq(@b, "c"). @a = @b == "c" is not
allowed.

| Data signatures                        |
|:---------------------------------------|
| eq( is this: Any, equal to that: Any ) |

| Call signatures                                                                                                                |
|:-------------------------------------------------------------------------------------------------------------------------------|
| eq( is this: Term ǁ Variable ǁ Header ǁ Function ǁ Reference, equal to that: Term ǁ Variable ǁ Header ǁ Function ǁ Reference ) |

| Purpose    | Value                          |
|:-----------|:-------------------------------|
| Main focus | eq() determines if lines match |
| Aliases    | equal, equals, eq              |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


