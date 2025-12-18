
## neq()

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

| Call signatures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| neq( is this: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ Function ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference), equal to that: [Term](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#term) ǁ [Variable](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#variable) ǁ [Header](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#header) ǁ Function ǁ [Reference](https://github.com/csvpath/csvpath/blob/main/docs/matching.md#reference) ) |

| Purpose    | Value                           |
|:-----------|:--------------------------------|
| Main focus | neq() determines if lines match |
| Aliases    | neq, not_equal_to               |

| Context          | Qualifier   |
|:-----------------|:------------|
| Match qualifiers | onmatch     |
| Value qualifiers | onmatch     |


