
Neq

Tests the equality of two values.

In most cases you will use == to test equality. However, in some cases
neq() gives more flexibility.

Moreover, in one case, you must use the function, not ==. Using neq()
is required in order to set a variable to the value of an equality
test.

In other words, to set @a equal to the equality test of @b to the
string "c", you must do: @a = neq(@b, "c"). @a = @b == "c" is not
allowed.

| Data signatures                         |
|:----------------------------------------|
| neq( is this: Any, equal to that: Any ) |

| Call signatures                                                                                                 |
|:----------------------------------------------------------------------------------------------------------------|
| neq( is this: Term|Variable|Header|Function|Reference, equal to that: Term|Variable|Header|Function|Reference ) |

| Purpose    | Value                           |
|:-----------|:--------------------------------|
| Main focus | neq() determines if lines match |
| Aliases    | neq, not_equal_to               |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


